import asyncio
import collections

import aiohttp
from aiohttp import web
import tqdm

from flags2_common import main, HTTPStatus, Result, save_flag

# default set low to avoid errors from remote site,
# such as 503 - Service Temporarily Unavailable
DEFAULT_CONCUR_REQ = 5
MAX_CONCUR_REQ = 1000


class FetchError(Exception):
    """
    このお手製の例外は、404以外のHTTPエラーやネットワーク関連の例外をラップしたもので、
    エラー時にcountry_codeを報告します。
    """
    def __init__(self, country_code):
        self.country_code = country_code


@asyncio.coroutine
def get_flag(base_url, cc):
    """
    get_flag関数はダウンロードした画像のバイト列を返します。
    HTTPステータスコードが404ならweb.HTTPNotFoundを、
    それ以外のコードならaiohttp.HttpProcessingErrorをそれぞれ上げます。
    """
    url = '{}/{cc}/{cc}.gif'.format(BASE_URL, cc=cc.lower())
    resp = yield from aiohttp.request('GET', url)
    if resp.status == 200:
        image = yield from resp.read()
        return image
    elif resp.status == 404:
        raise web.HTTPNotFound()
    else:
        raise aiohttp.HttpProcessingError(code=resp.status, message=resp.reason, headers=resp.headers)


@asyncio.coroutine
def download_one(cc, base_url, semaphore, verbose):
    """
    引数のsemaphoreにはasyncio.Semaphoreのインスタンスを指定します。
    このクラスは並行して行うリクエストの数を制限するための同期用メカニズムです。
    """

    try:
        # システムが全体としてはブロックされないようにするため、
        # semaphoreをyield from式の中でコンテキストマネージャとして使用します。
        # semaphoreのカウンタが上限に達しているとき、このコルーチンだけがブロックされます。
        with (yield from semaphore):

            # このwith文が終了すると、semaphoreのカウンタは1つ減じられます。
            # これで、同じsemaphoreオブジェクトで待機しているであろう他のコルーチンインスタンスのブロックが解除されます。
            image = yield from get_flag(base_url, cc)

    # 指定の国旗が見つからなかったときは、その旨をResultのステータスにセットします。
    except web.HTTPNotFound:
        status = HTTPStatus.not_found
        msg = 'not found'
    except Exception as exc:
        # 上記以外の例外はすべて、raise X from Yという構文を使って
        # 国別コードとひも付けられた元の例外を収容したFetchErrorとして報告されます。
        # この構文は、「PEP 3134 - Exception Chaining and Embedded Tracebacks」で導入されたものです。
        raise FetchError(cc) from exc
    else:
        # # 実際に国旗の画像をディスクに保存するのはこの関数です。
        # save_flag(image, cc.lower() + '.gif')
        # status = HTTPStatus.ok
        # msg = 'OK'

        # イベントループオブジェクトの参照を取得します。
        loop = asyncio.get_event_loop()

        # run_in_executorの第!引数にはExecutorインスタンスを指定します。
        # Noneならば、イベントループのデフォルトのスレッドプールExecutorが使用されます。
        # 残りの引数は呼び出し可能オブジェクトとその位置引数です。
        loop.run_in_executor(None, save_flag, image, cc.lower() + '.gif')
        
        status = HTTPStatus.ok
        msg = 'OK'

    if verbose and msg:
        print(cc, msg)

    return Result(status, cc)


@asyncio.coroutine
def downloader_coro(cc_list, base_url, verbose, concur_req):
    """
    このコルーチンはdownload_manyと同じ引数を受け取ります。
    しかし、これはコルーチン関数であり、download_manyのような普通の関数ではないため、
    mainから直接呼び出すことはできません。
    """

    counter = collections.Counter()

    # asyncio.Semaphoreを作成します。
    # このセマフォを共有するコルーチンは、最大concur_req個まで実行できます。
    semaphore = asyncio.Semaphore(concur_req)

    # download_oneコルーチンを1回呼び出すごとに1つずつコルーチンオブジェクトを作成し、リストにします。
    to_do = [download_one(cc, base_url, semaphore, verbose) for cc in sorted(cc_list)]

    # 完了するとFutureインスタンスを返すイテレータを取得します。
    to_do_iter = asyncio.as_completed(to_do)

    if not verbose:
        # このイテレータをtqdm関数でラップすることで、プログレスバーを表示します。
        to_do_iter = tqdm.tqdm(to_do_iter, total=len(cc_list))

    # 完了したFutureインスタンスに対し、以前のdownload_manyにあるものとほとんど同じループで反復処理します。
    # 変更の大半は、HTTPライブラリ間の例外処理の違い（requestsに対しここではaiohttp）によるものです。
    for future in to_do_iter:
        try:
            # asyncio.Futureの結果を取得するには、
            # future.result()を呼び出す代わりにyield fromを用いるのが最も簡単な方法です。
            res = yield from future

        # download_oneで発生する例外はどれも、元の例外をひも付けしたFetchErrorにラップされます。
        except FetchError as exc:
            # 例外FetchErrorから、エラーが発生した国別コードを取得します。
            country_code = exc.country_code
            try:
                # 元の例外（__cause__）からエラーメッセージの取得を試みます。
                error_msg = exc.__cause__.args[0]
            except IndexError:
                # 元の例外にエラーメッセージがなければ、ひも付けられた例外クラスの名前を
                # エラーメッセージとして用います。
                error_msg = exc.__cause__.__class__.__name__
            if verbose and error_msg:
                msg = '*** Error for {}: {}'
                print(msg.format(country_code, error_msg))
            status = HTTPStatus.error
        else:
            status = res.status

        # 結果を集計します。
        counter[status] += 1

    # 他のスクリプトと同じように、カウンタを返します。
    return counter


def download_many(cc_list, base_url, verbose, concur_req):
    """
    download_many関数はコルーチンをインスタンス化し、
    これをrun_until_completeを用いてイベントループに渡すだけです。
    """

    loop = asyncio.get_event_loop()
    coro = downloader_coro(cc_list, base_url, verbose, concur_req)
    counts = loop.run_until_complete(coro)

    # すべての作業が完了したら、イベントループを閉じ、countsを返します。
    loop.close()

    return counts


if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
