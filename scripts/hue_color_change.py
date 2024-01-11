import colorsys
import re
from pathlib import Path
import itertools
import sys


class HexMetadata:
    def __init__(self, src: Path, file: Path):
        self.src: Path = src
        self.file: Path = file
        self.lines: list[int] = []
        self.opts: list[str] = []
        self.opt_spans: list[tuple[int, int]] = []
        self.vals: list[str] = []
        self.val_spans: list[tuple[int, int]] = []
        self._get_metadata()

    def _get_metadata(self):
        line_match_regex = re.compile(
            '--[a-z0-9-]+: #([a-zA-Z0-9]{8}|[a-zA-Z0-9]{7}|[a-zA-Z0-9]{6}|[a-zA-Z0-9]{5}|[a-zA-Z0-9]{4}|[a-zA-Z0-9]{3}|[a-zA-Z0-9]{2}|[a-zA-Z0-9]{1});')
        opt_match_regex = re.compile('^--[a-z0-9-]+')
        hex_match_regex = re.compile(
            '#([a-zA-Z0-9]{8}|[a-zA-Z0-9]{7}|[a-zA-Z0-9]{6}|[a-zA-Z0-9]{5}|[a-zA-Z0-9]{4}|[a-zA-Z0-9]{3}|[a-zA-Z0-9]{2}|[a-zA-Z0-9]{1})')
        f = open(self.src, 'r')
        line_ctr = 0
        while True:
            line_ctr += 1
            line = f.readline()
            if not line:
                break
            m = line_match_regex.search(line)
            if m:
                
                m_opt = opt_match_regex.search(m.group())
                m_hex = hex_match_regex.search(m.group())

                self.lines.append(line_ctr)

                self.opts.append(m_opt.group())
                opt_span = (m.span()[0]+m_opt.span()[0], m.span()[0]+m_opt.span()[1])
                self.opt_spans.append(opt_span)
                    
                self.vals.append(m_hex.group())
                # print(m_hex.group())
                hex_span = (m.span()[0]+m_hex.span()[0], m.span()[0]+m_hex.span()[1])
                self.val_spans.append(hex_span)
        f.close()
    
    def _shift_hex_hue(self, hex_color: str, delta_hue: float) -> str:
        hex_color = hex_color.lstrip('#')
    
        hex_alpha = False
        if len(hex_color) < 6:
            for i in range(6 - len(hex_color)):
                hex_color += "0"
        elif len(hex_color) > 6:
            hex_alpha = True

        # Convert the hex color to RGB
        if hex_alpha:
            rgba = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
            h, l, s = colorsys.rgb_to_hls(rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0)
        else:
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

        s = 0.02
        h = (h + delta_hue) % 1.0

        if hex_alpha:
            new_rgba = tuple(int(value * 255) for value in colorsys.hls_to_rgb(h, l, s))
            new_rgba = new_rgba + tuple([rgba[3]])
            new_hex_color = "#{:02x}{:02x}{:02x}{:02x}".format(*new_rgba)
        else:
            new_rgb = tuple(int(value * 255) for value in colorsys.hls_to_rgb(h, l, s))
            new_hex_color = "#{:02x}{:02x}{:02x}".format(*new_rgb)
            
        # print(new_hex_color)
        # Convert the new RGB back to hex
        return new_hex_color

    def _find_indices(self, list_to_check: list, item_to_find) -> list[int]:
        indices = []
        for idx, value in enumerate(list_to_check):
            if value == item_to_find:
                indices.append(idx)
        return indices
    
    def shift_vals_hue(self, wl_opts: list[str], delta_hue: float):
        for wl_opt in wl_opts:
            occurrences_i = self._find_indices(self.opts, wl_opt)
            for occurrence_i in occurrences_i:
                # print(self.vals[occurrence_i])
                self.vals[occurrence_i] = self._shift_hex_hue(self.vals[occurrence_i], delta_hue)
                # print(self.vals[occurrence_i])
                

    def substitute_metadata(self):
        conts = ""
        f = open(self.src, 'r')
        line_ctr = 0
        while True:
            line_ctr += 1
            cur_line = f.readline()
            if not cur_line:
                break
            # print(f"{line_ctr} {self.lines[0]} ({len(self.lines)})")
            if len(self.lines) > 0 and self.lines[0] == line_ctr:
                cur_line_chars = list(cur_line)
                cur_line_chars[self.val_spans[0][0]:self.val_spans[0][1]] = self.vals[0]
                conts += ''.join(cur_line_chars)
                self.lines.pop(0)
                self.opts.pop(0)
                self.opt_spans.pop(0)
                self.vals.pop(0)
                self.val_spans.pop(0)
            else:
                conts += cur_line
        f.close()
        f = open(self.file, 'w')
        f.write(conts)
        f.close()
                
            
            
        # f.close()
        
            
        #         cur_line = list(conts[line-1])
        #         cur_line[val_span[0]:val_span[1]] = val
        #         repl_line = ''.join(cur_line)
        #         f.seek(line)
        
        
            

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: expected one argument with directory with custom_src.css and in which to generate custom.css")
        exit(1)
    delta_hue = 0.25;
    m = HexMetadata(Path(sys.argv[1], 'colors.scss'), Path(sys.argv[1], 'colors.scss'))
    m.shift_vals_hue(["--ls-primary-background-color",
        "--ls-secondary-background-color",
        "--ls-tertiary-background-color",
        "--ls-quaternary-background-color",
        "--ls-top-bar-background",
        "--ls-main-content-background",
        "--ls-left-sidebar-background",
        "--ls-dropdown-title-background",
        "--ls-settings-list-item-hover-background-color",
        "--ls-search-icon-color",
        "--ls-header-button-background",
        "--ls-create-button-color-sm",
        "--ls-create-button-color",
        "--ls-right-sidebar-content-background",
        "--ls-table-tr-even-background-color",
        "--ls-page-properties-background-color",
        "--ls-block-properties-background-color",
        "--ls-selection-background-color",
        "--ls-primary-background-color",
        "--ls-secondary-background-color",
        "--ls-tertiary-background-color",
        "--ls-quaternary-background-color",
        "--ls-top-bar-background",
        "--ls-main-content-background",
        "--ls-scrollbar-background-color",
        "--ls-dropdown-title-background",
        "--ls-settings-list-item-hover-background-color",
        "--ls-settings-dropdown-background",
        "--ls-settings-dropdown-link-item-background",
        "--ls-header-button-background",
        "--ls-left-sidebar-background",
        "--ls-create-button-color-sm",
        "--ls-create-button-color",
        "--ls-right-sidebar-content-background",
        "--ls-table-tr-even-background-color",
        "--ls-page-properties-background-color",
        "--ls-block-properties-background-color",
        "--ls-selection-background-color"], delta_hue)
    m.substitute_metadata()
    # print(f"{m.opts} {m.lines}, {m.spans}, {m.vals}")
    # for (opt, line, span, val) in zip(m.opts, m.lines, m.spans, m.vals):
    #     print(f"{opt} {val} {line} {span}")
