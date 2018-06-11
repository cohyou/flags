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
    # ここでは、人口最多5ヶ国のみを用います。
    cc_list = cc_list[:5]

    # max_workersを3にしました。これで保留されているfutureを出力から観察できます。
    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        to_do = []

        # 得られる結果の順序がバラバラになることが見た目でわかるよう、
        # 国別コードをアルファベット順にしてから反復処理します。
        for cc in sorted(cc_list):

            # executor.submitは実行すべき呼び出し可能オブジェクトをスケジューリングし、
            # 保留中の処理を表現するfutureを返します。
            future = executor.submit(download_one, cc)

            # 後からas_completedを介して取得できるよう、futuresをリストに格納します。
            to_do.append(future)

            # 国別コードとそれに対応したfutureを表示します。
            msg = 'Scheduled for {}: {}'
            print(msg.format(cc, future))

        results = []

        # futureが完了すると、その都度as_completedはインスタンスをyieldします。
        for future in futures.as_completed(to_do):

            # futureの結果を取得します。
            res = future.result()

            # futureとその結果を表示します。
            msg = '{} result: {!r}'
            print(msg.format(future, res))

            results.append(res)

    return len(results)
