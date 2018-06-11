import collections
from concurrent import futures

import requests

# プログレス表示ライブラリをインポートします。
import tqdm

# flags2_commonモジュールから関数を1つ、Enumを1つインポートします。
from flags2_common import main, HTTPStatus

# download_oneはflags2_sequentialのものを再利用します。
from flags2_sequential import download_one

# コマンドラインの-m/--max_reqは並行スレッドプールの最大数を指定するオプションです。
# デフォルトでは、並行して送信できるリクエストの最大数はここに示した30です。
# ただし、ダウンロードする国旗数が少なければ、実際に使用される数も少なくなります。
DEFAULT_CONCUR_REQ = 30

# 実際に用意されるプール数が大きくなりすぎないよう、
# 安全策としてMAX_CONCUR_REQ（1000）で制限します。
MAX_CONCUR_REQ = 1000


def download_many(cc_list, base_url, verbose, concur_req):
    counter = collections.Counter()

    # main関数は実際に用意するプール数を、MAX_CONCUR_REQ、国旗の数（cc_listの要素数）、
    # そして-m/--max_reqコマンドラインオプションで指定された値のうちの最小の値から定めます。
    # この値は、この関数が呼ばれるときに第4引数として引き渡されます（concur_req）。
    # そして、max_workersにこの値を指定してexecutorを作成します。
    # これにより、余分なスレッドが作成されないようになります。
    with futures.ThreadPoolExecutor(max_workers=concur_req) as executor:

        # このdictはエラー報告用に、Futureインスタンスと国別コードをマップします。
        # Futureインスタンスはそれぞれのダウンロードを表現しています。
        to_do_map = {}

        # 国別コードのアルファベット順のリストに対して反復処理します。
        # 結果が得られる順番は、何よりも、HTTPレスポンスがいつ返ってくるかに依存します。
        # しかし、concur_reqで指定されたスレッドプール数が国旗数（len(cc_list)）よりもずっと小さいときは、
        # ダウンロードがアルファベット順に処理されることもあります。
        for cc in sorted(cc_list):

            # executor.submitを1回呼び出すと、
            # 呼び出し可能オブジェクトの実行を1つスケジュールし、Futureインスタンスが返されます。
            # 第1引数が呼び出し可能オブジェクト（ここではdownload_one）で、
            # 残りの引数はそのオブジェクトが受け取る引数です。
            # （国別コードのcc、ベースURLのbase_url、verbose）
            future = executor.submit(download_one, cc, base_url, verbose)

            # 得られたfutureと国別コードをdictに格納します。
            to_do_map[future] = cc

        # futures.as_completedはFutureインスタンスのイテレータを返します。
        # 各インスタンスは完了と同時にyieldされます。
        done_iter = futures.as_completed(to_do_map)

        if not verbose:
            # verboseモードで実行されていなければ、
            # 関数tqdmにas_completedから得られた結果を指定し、プログレスバーを表示します。
            # done_iterにはlenがないので、これだけでは残りの作業業を確定できません。
            # そこで、先に説明したようにオプション引数のtotal=で予想される要素数をtqdmに伝えなければなりません。
            done_iter = tqdm.tqdm(done_iter, total=len(cc_list))

        # 完了したFutureインスタンスに対して反復処理します。
        for future in done_iter:
            try:
                # Futureインスタンスのresultメソッドを呼び出すと、
                # この呼び出し可能オブジェクトが返した値が返されるか、
                # 実行時にキャッチされた例外が何であれ上げられます。
                # このメソッドは、解決するまで処理をブロックすることがあります。
                # しかし、この例ではas_completedは完了したFutureインスタンスを返すだけなので、
                # ブロックはされません。
                res = future.result()

            # 上げられる可能性のある例外を処理します。
            # 本関数のこれ以降の部分は、1行を除いて、逐次型のdownload_manyと同じです。
            except requests.exceptions.HTTPError as exc:
                error_msg = 'HTTP {res.status_code} - {res.reason}'
                error_msg = error_msg.format(res=exc.response)
            except reqeusts.exceptions.ConnectionError as exc:
                error_msg = 'Connection error'
            else:
                error_msg = ''
                status = res.status

            if error_msg:
                status = HTTPStatus.error
            counter[status] += 1
            if verbose and error_msg:
                # エラーメッセージに必要なデータを得るため、
                # その時点のFutureインスタンス（future）をキーに指定してto_do_mapから国別コードを取得します。
                # 逐次型スクリプトでは国別コードのリストに対して反復処理したため、
                # このような処理をせずともその時点でのccが入手できました。
                # ここでは、Futureインスタンスに対して反復処理しているため、to_do_mapを用います。
                cc = to_do_map[future]
                print('*** Error for {}: {}'.format(cc, error_msg))

    return counter

if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
