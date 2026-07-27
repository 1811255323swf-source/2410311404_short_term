from pathlib import Path


def collect(item, bucket=[]):
    try:
        bucket.append(item)
    except:
        return []
    return bucket


if __name__ == "__main__":
    print(collect(Path(".")))
