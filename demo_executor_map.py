from time import sleep, strftime
from concurrent import futures


def display(*args):
    """
    この関数は先頭に[HH:MM:SS]形式のタイムスタンプ、
    続けて引数に指定されたものなら単純に何でも出力します。
    """
    print(strftime('[%H:%M:%S]'), end=' ')
    print(*args)


def loiter(n):
    """
    loiterは起動するとメッセージを表示し、続けてn秒間スリープ状態に入り、
    それが終わるとメッセージを表示する以外何もしません。
    メッセージはn個分のタブでインデントされます。
    """
    msg = '{}loiter({}): doing nothing for {}s...'
    display(msg.format('\t'*n, n, n))
    sleep(n)
    msg = '{}loiter({}): done.'
    display(msg.format('\t'*n, n))

    # 演算結果の取得方法を確認できるよう、loiterがn * 10を返すようにしています。
    return n * 10


def main():
    display('Script starting.')

    # スレッドを3本用意したThreadPoolExecutorを作成します。
    executor = futures.ThreadPoolExecutor(max_workers=3)

    # executorに5つのタスクを登録します。スレッドが3本しかないので、
    # 直ちに起動するのはそのうち3つけだけです(loiter(0)、loiter(1)、loiter(2))。
    # この呼び出しはノンブロッキングです。
    results = executor.map(loiter, range(5))

    # 起動したexecutor.mapのresultsを直ちに表示します。
    # 出力結果が示すように、これはジェネレータです。
    display('results:', results)

    display('Waiting for individual results:')

    # forループにあるenumerateは暗黙的にnext(results)を呼び出します。
    # next(results)は続けて、Futureインスタンスの_fの_f.result()を内部で呼び出します。
    # この_fは最初に呼び出したloiter(0)を表現しています。
    # resultメソッドはFutureインスタンスが完了するまで処理をブロックします。
    # したがって、次のresultが用意できるまでループの反復処理は待機しなければなりません。
    for i, result in enumerate(results):
        display('result {}: {}'.format(i, result))

main()
