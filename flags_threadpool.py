from concurrent import futures

# flagsモジュールの関数をいくつか再利用します。
from flags import save_flag, get_flag, show, main

# ThreadPoolExecutorで利用できる最大スレッド数です。
MAX_WORKERS = 20


def download_one(cc):
    """
    画像を1枚ダウンロードする関数です。スレッドはそれぞれこれを実行します。
    """
    image = get_flag(cc)
    show(cc)
    save_flag(image, cc.lower() + '.gif')
    return cc


def download_many(cc_list):
    # ワーカースレッド数を設定します。最大スレッド数（MAX_WORKERS）と
    # 実際の処理の対象となる要素の数のどちらか小さい方の値を使用すれば、不要なスレッドは作成されません。
    workers = min(MAX_WORKERS, len(cc_list))

    # ワーカースレッド数を指定してThreadPoolExecutorをインスタンス化します。
    # executor.__exit__メソッドから呼び出されるexecutor.shutdown(wait=True)は、
    # すべてのスレッドが完了するまでブロックされます。
    with futures.ThreadPoolExecutor(workers) as executor:

        # mapメソッドは組み込み関数のmapと似ていますが、
        # 指定のdownload_one関数が複数のスレッドから並行して呼び出されるところが異なります。
        # このメソッドは、それぞれの関数が返した値を反復処理で取得できるジェネレータを返します。
        res = executor.map(download_one, sorted(cc_list))

    # 得られた結果の数を返します。スレッド化された呼び出しが例外を上げると、
    # イテレータから対応する戻り値を取得しようとした暗黙的なnext()呼び出しの例外として、ここで上げられます。
    return len(list(res))


    if __name__ == '__main__':
        # download_manyの改訂版を指定して、flagsモジュールのmain関数を呼び出します。
        main(download_many)
