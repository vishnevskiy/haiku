from haml import HAML

if __name__ == '__main__':
    with open('haml.haml') as f:
        print HAML(f.read())