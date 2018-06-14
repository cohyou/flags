"""
コルーチンによるスピナー
"""

import asyncio
import itertools
import sys


# asyncioで使うつもりのあるコルーチンは、@asyncio.coroutineで装飾すべきです。
# 必須ではありませんが、やっておくべき措置です。詳細はこのコードのあとで説明します。
@asyncio.coroutine
def spin(msg):
    """
    スレッドを終了させるために以前の関数spinは引数signalを用いましたが、
    ここではそれは必要ありません。
    """

    write, flush = sys.stdout.write, sys.stdout.flush
    for char in itertools.cycle('|/-\\'):
        status = char + ' ' + msg
        write(status)
        flush()
        write('\x08' * len(status))
        try:
            # イベントループをブロックすることなくスリープさせるには、
            # 単純にtime.sleep(.1)とするのではなく、yield from asyncio.sleep(.1)と書きます。
            yield from asyncio.sleep(.1)

        # spinが起動したあとでasyncio.CancelledErrorが上がってきたとしたら、
        # それはキャンセルが要求されたためです。そこで、ループを抜けます。
        except asyncio.CancelledError:
            break
    write(' ' + len(status) + '\x08' * len(status))


@asyncio.coroutine
def slow_function():
    """
    ここでのslow_functionはコルーチンです。
    そこで、このコルーチンがあたかもI/O処理で待機しているかのように振る舞っている間、
    yield fromでイベントループを進めます。
    """

    # pretend waiting a long time for I/O

    # このyield from asyncio.sleep(3)はメインループに制御フローを渡し、
    # sleepによる待機が完了したらコルーチンを再開します。
    yield from asyncio.sleep(3)

    return 42


@asyncio.coroutine
def supervisor():
    """
    ここでのsupervisorもコルーチンなので、yield fromからslow_functionを駆動できます。
    """

    # asyncio.async(...)はspinコルーチンを起動するようスケジュールします。
    # 直ちに戻ってくるTaskオブジェクトにはspinがラップされています。
    spinner = asyncio.async(spin('thinking!'))

    # Taskオブジェクトを表示します。
    # 出力は「<Task pending coro=<spin() running at spinner_asyncio.py:6>>」のようになります。
    print('spinner object:', spinner)

    # slow_function()を駆動します。終了したら、返ってきた値を取得します。
    # 終了を待つ間も、イベントループは走り続けます。
    # slow_functionはその中でyield from asyncio.sleep(3)を使用しているので、
    # 制御をメインループに返すからです。
    result = yield from slow_function()

    # Taskオブジェクトはキャンセルできます。
    # キャンセルされると、コルーチンが休止しているyieldの行でasyncio.CancelledErrorが上がってきます。
    # コルーチンは例外をキャッチしてもよいですし、キャンセルを遅らせたり、キャンセルしないようにしたりもできます。
    spinner.cancel()
    
    return result


def main():
    # イベントループへの参照を取得します。
    loop = asyncio.get_event_loop()

    # supervisorコルーチンが完了するまで駆動します。
    # コルーチンの戻り値がこの呼び出しの戻り値となります。
    result = loop.run_until_complete(supervisor())

    loop.close()

    print('Answer:', result)


if __name__ == '__main__':
    main()
