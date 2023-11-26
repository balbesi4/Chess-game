import chess
import chess.engine

#либа вроде вообще все умеет
# Тут охереть говна кусок, а не код, но пропробуй встроить все это дерьмо


engine = chess.engine.SimpleEngine.popen_uci("stockfish")
for row in bord:
    free_row = 0
    s = ''
    for cell in row:
        val = cell.value
        # Вот эту залупу перепиши плз
        cell.is_empty():
            free_row += 1
        else:
            if free_row > 0:
                s += str(free_row)
                free_row = 0
            if cell.name == 'pawn':
                if val > 0:
                    s += 'P'
                else:
                    s += 'p'
            if cell.name == 'knight':
                if val > 0:
                    s += 'N'
                else:
                    s += 'n'
            if cell.name == 'bishop':
                if val > 0:
                    s += 'B'
                else:
                    s += 'b'
            if cell.name == 'rook':
                if val > 0:
                    s += 'R'
                else:
                    s += 'r'
            if cell.name == 'queen':
                if val > 0:
                    s += 'Q'
                else:
                    s += 'q'
            if cell.name == 'king':
                if val > 0:
                    s += 'K'
                else:
                    s += 'k'
    if free_row > 0:
        s += str(free_row)
    s += '/'
#убрали последний слэш
s = s[:-1]
# b/w за цвет
s += f' {color} '
s += 'KQkq - 0 1'

# Вот эта вот херня должна выдать лучший ход
print(engine.play(s, chess.engine.Limit(time=2.0)).move)