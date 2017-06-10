def callme():
    n = 0
    while True:
        print 'call %s' % n
        x = yield n
        n += 1
        print 'you call me %s' % x

    return



if __name__ == '__main__':
    c = callme()
    print c.send(None)
    print c.send('hello')
    print 'let me think...'
    print c.send('world')
    print c.send(None)
