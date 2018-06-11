import os
import time
import sys

# requestsライブラリをインポートします（後述のヒント参照）。これは標準ライブラリではないので、
# 規約に従って標準ライブラリモジュールのos、time、sysのあとでインポートし、
# 空行を挟むことで標準ライブラリと区別します。
import requests

# 人口の降順で並べた、人口最多20ヶ国のISO3166国別コードのリストを用意します。
POP20_CC = ('CN IN US ID BR PK NG BD RU JP '
            'MX PH VN ET DG DE IR TR CD FR').split()

# 国旗の画像があるウェブサイトです。
BASE_URL = 'http://flupy.org/data/flags'

# 画像を保存するローカルディレクトリです。
DEST_DIR = 'downloads/'


def save_flag(img, filename):
    """
    バイト配列であるimgを単純にDEST_DIRのfilenameに保存します。
    """
    path = os.path.join(DEST_DIR, filename)
    with open(path, 'wb') as fp:
        fp.write(img)


def get_flag(cc):
    """
    与えられた国別コードからURLを作成し、その画像をダウンロードし、
    レスポンスのバイナリコンテンツを返します。
    """
    url = '{}/{cc}/{cc}.gif'.format(BASE_URL, cc=cc.lower())
    resp = requests.get(url)
    return resp.content


def show(text):
    """
    文字列を表示します。同じ行で進行状況を示すには、sys.stdoutをフラッシュしなければなりません。
    Pythonは通常、改行を待ってstdoutバッファをフラッシュするからです。
    """
    print(text, end=' ')
    sys.stdout.flush()


def download_many(cc_list):
    """
    関数download_manyは、あとで示す並行処理の実装と比較するときのベースラインになります。
    """

    # 国別コードをアルファベット順にソートしたリストに対してループします。
    # これで、元の順序通りに出力されていくことを明示できます。
    # 最後に、ダウンロードした国別コードの数を返します。
    for cc in sorted(cc_list):
        image = get_flag(cc)
        show(cc)
        save_flag(image, cc.lower() + '.gif')

    return len(cc_list)


def main(download_many):
    """
    mainはdownload_manyの実行に要した時間を測定し、それを報告します。
    """
    t0 = time.time()
    count = download_many(POP20_CC)
    elapsed = time.time() - t0t0msg = '\n{} flags downloaded in {:.2f}s'
    print(msg.format(count, elapsed))


if __name__ == '__main__':
    # mainを呼び出す時は、ここでdownloads_manyを指定しているように、
    # ダウンロードを実行する関数を引数として指定しなければなりません。
    # これで、異なる実装をしたdownload_manyも呼び出せるライブラリ関数として利用できます。
    main(download_many)
