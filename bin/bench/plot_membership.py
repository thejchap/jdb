from os import path, listdir
import json
from statistics import mean
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

_DIRNAME = path.dirname(__file__)
_PATH = path.join(_DIRNAME, "data", "membership")


def _main():
    """plot results"""

    result = {}
    dicts = {}

    for version in listdir(_PATH):
        dicts[version] = {}

        for folder in listdir(path.join(_PATH, version)):
            if path.isfile(path.join(_PATH, version, folder)):
                continue

            dicts[version][folder] = []

            for file in listdir(path.join(_PATH, version, folder)):
                if not path.isfile(path.join(_PATH, version, folder, file)):
                    continue

                with open(path.join(_PATH, version, folder, file), "r") as jsonfile:
                    dicts[version][folder].append(json.loads(jsonfile.read()))

    for version, vals in dicts.items():
        result[version] = {}
        for grp, dicts in vals.items():
            res = {}
            for dic in dicts:
                for key in dic.keys():
                    if key not in res:
                        res[key] = []
                    res[key].append(dic[key])
            result[version][grp] = res

    for version, vals in result.items():
        for grp, res in vals.items():
            for key in res:
                result[version][grp][key] = mean(result[version][grp][key])

    for version, datas in sorted(result.items()):
        for key, data in datas.items():
            plt.plot(
                list(map(lambda x: round(float(x), 2), data.keys())),
                list(data.values()),
                label=f"{version} ({key})",
            )

    plt.gca().yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(0.5))
    plt.legend(loc="upper right")
    plt.ylabel("infected nodes")
    plt.xlabel("time in seconds")
    plt.show()


if __name__ == "__main__":
    _main()
