word_ = [0] * 25 # Initializing an array with 25 cells

n = int(input())

if n > 25:
    exit(-1) # Pep/9 translation: STOP

i = 0
while i < n:
    word_[i] = int(input())
    i = i + 1

i = 0
while i < n:
    print(word_[i])
    i = i + 1






