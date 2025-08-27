#!/usr/bin/env python

# ************************************************************************
# * Copyright (c) 2022 Yorik van Havre <yorik@uncreated.net>             *
# *                                                                      *
# * This program is free software; you can redistribute it and/or modify *
# * it under the terms of the GNU Lesser General Public License (LGPL)   *
# * as published by the Free Software Foundation; either version 2 of    *
# * the License, or (at your option) any later version.                  *
# * for detail see the LICENCE text file.                                *
# *                                                                      *
# * This program is distributed in the hope that it will be useful,      *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of       *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
# * GNU Library General Public License for more details.                 *
# *                                                                      *
# * You should have received a copy of the GNU Library General Public    *
# * License along with this program; if not, write to the Free Software  *
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
# * USA                                                                  *
# *                                                                      *
# ************************************************************************

"""This script produces an index.html file and an images/ folder which
shows and allows to download the contents of the library"""

from pathlib import Path
import zipfile
import hashlib
import urllib.parse

# path definitions
homefolder = Path.cwd()
imagefolder = Path("thumbnails")
htmlfile = homefolder / "index.html"
template_path = homefolder / "index_template.html"
baseurl = "https://github.com/FreeCAD/FreeCAD-library/blob/master/"
excludelist = {"thumbnails"}

# icons
defaulticon = imagefolder / "freecad-document.svg"
gridicon = imagefolder / "icon-grid.svg"
listicon = imagefolder / "icon-list.svg"
stepicon = imagefolder / "icon-grey.svg"
brepicon = imagefolder / "icon-blue.svg"
stlicon = imagefolder / "icon-green.svg"
collapseicon = imagefolder / "icon-right.svg"
expandicon = imagefolder / "icon-down.svg"

# HTML template is stored externally in index_template.html

def build_html(dirpath: Path, level: int = 1) -> str:

    """Walk a directory and build cards from its contents"""

    html = ""
    if dirpath.is_dir():
        html += build_title(dirpath, level)
        if level > 1:
            html += '<div class="collapsable hidden">\n'
        try:
            nodes = [p for p in dirpath.iterdir() if not p.name.startswith(".") and p.name not in excludelist]
        except OSError as err:
            print(f"Cannot access {dirpath}: {err}")
            return html
        dirs = sorted(p for p in nodes if p.is_dir())
        files = sorted(p for p in nodes if p.suffix.lower() == ".fcstd")
        for fpath in dirs:
            html += build_html(fpath, level + 1)
        if files:
            html += '<div class="cards">\n'
            for fpath in files:
                html += build_card(fpath)
            html += '</div>\n'
        if level > 1:
            html += '</div>\n'
    return html


def build_title(dirpath: Path, level: int) -> str:

    """Build an HTML title from a path"""

    if level == 1:
        # do not print the first-level title
        return ""
    sl = str(level)
    sn = f'<img class="hicon" src="{clean_path(collapseicon)}"/>'
    sn += dirpath.name
    if level < 7:
        title = '<h' + sl + ' onclick="collapse(this.children[0])">'
        title += sn + '</h' + sl + '>\n'
    else:
        title = '<div class="h' + sl + '" onclick="collapse(this.children[0])">'
        title += sn + '</div>\n'
    return title


def build_card(filepath: Path) -> str:

    """Build an HTML card for a given file"""

    print("Building card for", filepath)
    html = ""
    if filepath.exists():
        basename = filepath.with_suffix("")
        name = basename.name
        iconpath = get_icon(filepath)
        raw = "?raw=true"
        fileurl = baseurl + clean_path(filepath) + raw
        html += '<div class="card">'
        html += f'<a title="FCSTD version" href="{fileurl}">'
        html += f'<img class="icon" src="{clean_path(iconpath)}"/>'
        html += f'<div class="name">{name}</div>'
        html += '</a>'
        html += '<div class="links">'
        exts = {
            'STEP': (".stp", ".step", ".STP", ".STEP"),
            'BREP': (".brp", ".brep", ".BRP", ".BREP"),
            'STL': (".stl", ".STL"),
        }
        icons = {
            'STEP': stepicon,
            'BREP': brepicon,
            'STL': stlicon,
        }
        for name_key, ext_list in exts.items():
            for ext in ext_list:
                ext_path = basename.with_suffix(ext)
                if ext_path.exists():
                    exturl = baseurl + clean_path(ext_path) + raw
                    html += f' <a href="{exturl}" title="{name_key} version">'
                    html += f'<img src="{clean_path(icons[name_key])}"/>'
                    html += '</a>'
                    break
        html += '</div>'  # links
        html += '</div>\n'  # card
    return html


def get_icon(filepath: Path) -> Path:

    """Return a thumbnail image path for a given file path"""

    iconname = get_hashname(filepath)
    iconurl = imagefolder / iconname
    iconpath = homefolder / iconurl
    try:
        with zipfile.ZipFile(filepath) as zfile:
            if "thumbnails/Thumbnail.png" in zfile.namelist():
                data = zfile.read("thumbnails/Thumbnail.png")
                with open(iconpath, "wb") as thumb:
                    thumb.write(data)
            else:
                return defaulticon
    except Exception as err:
        print(f"Cannot extract icon from {filepath}: {err}")
        return defaulticon
    return iconurl if iconpath.exists() else defaulticon


def get_hashname(filepath: Path) -> str:

    """Create a png filename for a given file path"""

    cleaned = clean_path(filepath)
    return hashlib.md5(cleaned.encode()).hexdigest() + ".png"


def clean_path(filepath: Path) -> str:

    """Clean a file path into subfolder/subfolder/file form"""

    try:
        filepath = filepath.resolve()
    except Exception:
        filepath = Path(filepath)
    try:
        filepath = filepath.relative_to(homefolder)
    except ValueError:
        pass
    filepath_str = str(filepath).replace("\\", "/")
    if filepath_str.startswith("/"):
        filepath_str = filepath_str[1:]
    return urllib.parse.quote(filepath_str)


if __name__ == "__main__":
    template = template_path.read_text()
    html = build_html(homefolder)
    html = template.replace("<!--contents-->", html)
    html = html.replace("<!--listicon-->", clean_path(listicon))
    html = html.replace("<!--gridicon-->", clean_path(gridicon))
    html = html.replace("<!--collapseicon-->", clean_path(collapseicon))
    html = html.replace("<!--expandicon-->", clean_path(expandicon))
    with htmlfile.open("w") as index:
        index.write(html)
    print("Saving", htmlfile, "... All done!")
