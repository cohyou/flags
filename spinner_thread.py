"""
スレッドによるスピナー
"""

import threading
import itertools
import time
import sys


# この簡素な可変オブジェクトクラスに、外部からスレッドを制御するための属性語を定義します。
class Signal:
    go = True


def spin(msg, signal):
    write, flush = sys.stdout.write, sys.stdout.flush

    # itertools.cycleは与えられたシーケンスの要素を循環しながら永遠に生成するため、
    # 無限ループが構成されます。
    for char in itertools.cycle('|/-\\')
        status = char + ' ' + msg
        write(status)
        flush()
        # これが、テキストアニメーションのトリックです。
        # カーソルを後方に動かすために、バックスペース文字（\x08）を使っています。
        write('\x08' * len(status))
        time.sleep(.1)
        if not signal.go:
            break
    # 表示行を消去するため、スペースで上書きした上でカーソルを先頭に移動します。
    write(' ' * len(status) + '\x08' * len(status))


# とても計算量の多い関数だとしましょう。
def slow_function():
    # pretend waiting a long time for I/O
    # sleepを呼び出すとメインスレッドがブロックされます。
    # ここで重要なのは、GILが解除されるので、セカンダリスレッドはそれでも続行できるというところです。
    time.sleep(3)
    return 42

# この関数はセカンダリスレッドをスタートし、そのスレッドオブジェクトを表示し、
# 計算量の多い処理を実行して、最後にスレッドを終了させます。
def supervisor():
    signal = Signal()
    spinner = threading.Thread(target=spin, args=('thinking!', signal))

    # この関数はセカンダリスレッドを表示します。
    # 出力は「<Thread(Thread-1, initial)>」のようになります。
    print('spinner object:', spinner)

    # セカンダリスレッドを開始します。
    spinner.start()

    # slow_functionをスタートしたので、メインスレッドがブロックされます。
    # その間も、セカンダリスレッドで走っているスピナーは文字をくるくるまわし続けます。
    result = slow_function()

    # 関数spinにあるforループから抜けるため、signalの状態を変更します。
    signal.go = False

    # spinnerスレッドが終了するまで待機します。
    spinner.join()

    return result


def main():
    # 関数supervisorを起動します。
    result = supervisor()
    print('Answer:', result)


if __name__ == '__main__':
    main()
