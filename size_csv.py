# Usage:
#
#  python3 size_csv.py api_level/31/*.(otf|ttf|ttc)
#

import csv
import os
import sys

from pathlib import Path

from fontTools.ttLib import TTFont


def main(argv):
    font_dict = {}
    total_filesize = 0
    total_font_count = 0
    fields = ["Font", "Size (B)", "Version"]
    csv_data_list = []

    for fontpath in argv:
        size = os.path.getsize(fontpath)
        total_filesize += size
        total_font_count += 1
        font_dict[os.path.basename(fontpath)] = size


    for key in sorted(font_dict):
        fontpath = Path(f"api_level/31/{key}")
        if fontpath.suffix == ".ttc":
            tt = TTFont(fontpath, fontNumber=0)
        else:
            tt = TTFont(fontpath)
        
        namerecord_list = tt["name"].names
        # read in name records
        for record in namerecord_list:
            if record.nameID == 5:
                version = record.toUnicode()
                # remove any commas in the nameID 5 version string
                # this is used in a comma delimited output format and we can't include them
                version = version.replace(",", " ")
                break

        print(f"{key} : {font_dict[key]}, {version}")
        csv_data_list.append({
            fields[0]: key, 
            fields[1]: font_dict[key], 
            fields[2]: version
        })

    print(f"\nTotal size: {total_filesize}")
    print(f"Total fonts: {total_font_count}")

    with open("fontsize.csv", "w") as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
        csvwriter.writeheader()
        csvwriter.writerows(csv_data_list)


if __name__ == "__main__":
    main(sys.argv[1:])
