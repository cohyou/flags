"""
asyncioとaiohttpによる非同期ダウンロードスクリプト
"""

import asyncio

# 標準ライブラリにはないaiohttpは、
# あらかじめインストールしておかなければなりません。
import aiohttp

# 以前用意したflagsモジュールの関数をいくつか再利用します。
from flags import BASE_URL, save_flag, show, main


# コルーチンは@asyncio.coroutineを用いて装飾しなければなりません。
@asyncio.coroutine
def get_flag(cc):
    url = '{}/{cc}/{cc}.gif'.format(BASE_URL, cc=cc.lower())

    # ブロッキング型の処理はコルーチンとして実装されており、
    # これらはyield fromを介してデリゲートされるので、非同期的に実行されます。
    resp = yield from aiohttp.request('GET', url)

    # レスポンスの中身は、先のとは別の非同期処理で読み込みます。
    image = yield from resp.read()

    return image


@asyncio.coroutine
def download_one(cc):
    """
    download_oneもyield fromを用いているので、コルーチンでなければなりません。
    """

    # 以前実装したdownload_oneと異なるのは、
    # この行に加わっている「yield from」の部分だけで、他は全く同じです。
    image = yield from get_flag(cc)

    show(cc)
    save_flag(image, cc.lower() + '.gif')

    return cc


def download_many(cc_list):

    # 内部にあるイベントループ実装への参照を取得します。
    loop = asyncio.get_event_loop()

    # 取得する国旗ごとにdownload_one関数をそれぞれ呼び出し、
    # ジェネレータオブジェクトのリストを作成します。
    to_do = [download_one(cc) for cc in sorted(cc_list)]

    # wait（待て）という名前に反して、この関数はブロッキング型ではありません。
    # 渡されたすべてのコルーチンが完了した時に完了するコルーチンです。
    # これがwaitのデフォルト動作です（すぐあとで説明します）。
    wait_coro = asyncio.wait(to_do)

    # wait_coroが完了するまでイベントループを実行します。
    # イベントループの実行中にスクリプトがブロックするのがここです。
    # run_until_completeの2番目の戻り値は利用しません。
    # その理由はあとで説明します。
    res, _ = loop.run_until_complete(wait_coro)

    # イベントループを終了させます。
    loop.close()

    return len(res)


if __name__ == '__main__':
    main(download_many)
