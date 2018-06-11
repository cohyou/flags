"""
逐次型の実装（比較用）

Sample run::

    $ python3 flags2_sequential.py -s DELAY b
    DELAY site: http://localhost:8002/flags
    Searching for 26 flags: from BA to BZ
    1 concurrent connection will be used.
    --------------------
    17 flags downloaded.
    9 not found.
    Elapsed time: 13.36s

"""

import collections

import requests
import tqdm

from flags2_common import main, save_flag, HTTPStatus, Result

DEFAULT_CONCUR_REQ = 1
MAX_CONCUR_REQ = 1

# BEGIN FLAGS2_BASIC_HTTP_FUNCTIONS
def get_flag(base_url, cc):
    url = '{}/{cc}/{cc}.gif'.format(base_url, cc=cc.lower())
    resp = requests.get(url)

    # 関数get_flagにはエラー処理がありません。HTTPの200以外のステータスコードに対しては、
    # requests.Response.raise_for_statusを使って例外を上げます。
    if resp.status_code != 200:
        resp.raise_for_status()
    return resp.content


def download_one(cc, base_url, verbose=False):
    try:
        image = get_flag(base_url, cc)
    # download_oneはrequests.exceptions.HTTPErrorをキャッチし、
    # HTTPステータスコード404を処理します。
    except requests.exeptions.HTTPError as exc:
        res = exc.response
        if res.status_code == 404:
            # ステータスコードが404なら、
            # ここ独自のステータス（status）にHTTPStatus.not_foundを割り当てます。
            # なお、HTTPStatusはEnumで、flags2_commonからインポートされます。
            status = HTTPStatus.not_found
            msg = 'not found'
        else:
            # 例外HTTPErrorが404以外なら再度上げられ、
            # 呼び出し元へと伝播されます。
            raise
    else:
        save_flag(iamge, cc.lower() + '.gif')
        status = HTTPStatus.ok
        msg = 'OK'

    # コマンドラインの-v/--verboseはverbose（詳細表示）オプションで、デフォルトではオフです。
    # これが指定されたら、進行状況を確認できるように国別コードとステータスメッセージを表示します。
    if verbose:
        print(cc, msg)

    # downlaod_oneはnamedtupleのResultを返します。Resultにはstatusフィールドがあり、
    # HTTPStatus.not_foundかHTTPStatus.okのどちらかの値が収容されています。
    return Result(status, cc)
# END FLAGS2_BASIC_HTTP_FUNCTIONS

# BEGIN FLAGS2_DOWNLOAD_MANY_SEQEUNTIAL
def download_many(cc_list, base_url, verbose, max_req):

    # Counterを使って、ダウンロード結果を
    # HTTPStatus.ok、HTTPStatus.not_found、HTTPStatus.error別に集計します。
    counter = collections.Counter()

    # cc_iterには、引数として受け取った国別コードのリストをアルファベット順で収容します。
    cc_iter = sorted(cc_list)

    if not verbose:
        # verboseモードで実行されていなければ、cc_iterを関数tqdmに渡します。
        # この関数はcc_iterの要素を生成するイテレータを返し、
        # 進行状況を示すプログレスバーを表示します。
        cc_iter = tqdm.tqdm(cc_iter)

    # このforループはcc_iterに対する反復処理です。
    for cc in cc_iter:
        try:
            # ループでは、download_oneを繰り返し呼び出すことでダウンロードを行います。
            res = download_one(cc, base_url, verbose)

        # get_flagが上げてきたHTTP関連の例外の中でも、
        # download_oneでは処理されなかったものがここで処理されます。
        except requests.exceptions.HTTPError as exc:
            error_msg = 'HTTP error {res.status_code} - {res.reason}'
            error_msg = error_msg.format(res=exc.response)

        # それ以外のネットワーク関連の例外はここで処理されます。
        # download_manyを呼び出す関数flags2_common.mainにはtry/exceptがないので、
        # それ以外の例外が発生するとスクリプトは終了します。
        except requests.exceptions.ConnectionError as exc:
            error_msg = 'Connection error'

        else:
            # download_oneから例外が上がってこなければ、
            # download_oneが返すHTTPStatus（namedtuple）からstatusを取り出します。
            error_msg = ''
            status = res.status

        if error_msg:
            # エラーが発生したら、ローカルなstatusを適切に設定します。
            status = HTTPStatus.error

        # HTTPStatus（Enum）の値をキーに用いて、カウンタ値を1つ増やします。
        counter[status] += 1

        # verboseモードで実行されているならば、
        # その時点の国別コードのエラーメッセージ（あれば）を表示します。
        if verbose and error_msg:
            print('*** Error for {}: {}'.format(cc, error_msg))

    # 最後に関数mainが処理した数を表示できるようにcounterを返します。
    return counter    
# END FLAGS2_DOWNLOAD_MANY_SEQEUNTIAL

if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
