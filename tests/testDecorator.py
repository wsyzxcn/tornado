def deco(func):
    print 'run deco'

@deco
def test():
    pass

if __name__ == '__main__':
    pass