# 충돌 판정에 쓰는 공용 함수. 사각형은 (left, bottom, right, top)


def overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
