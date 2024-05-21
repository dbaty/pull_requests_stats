import os
import pygal

import datetime


# Taken verbatim from https://github.com/Kozea/pygal/issues/516#issuecomment-1596130653
class LineBar(pygal.Line, pygal.Bar):
    """Class that renders primary data as line, and secondary data as bar."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secondary_range = kwargs.get("secondary_range")

    def add(self, label, data, **kwargs):
        # We add an empty data point, because otherwise the secondary series (the bar chart)
        # would overlay the axis.
        super().add(label, data + [None], **kwargs)

    def _fix_style(self):
        # We render the plot twice, this time to find the width of a single bar
        # Would that you could just offset things in SVG by percentages without nested SVGs or similar dark magic.
        bar_width = int(
            float(
                self.render_tree().findall(".//*[@class='bar']/rect")[0].attrib["width"]
            )
        )
        line_offset = str(bar_width / 2 + 6)
        bar_offset = str(bar_width + 3)
        added_css = """
          {{ id }} g.series .line  {
            transform: translate({line_offset}px, 0);
          }
          {{ id }} g.series .dots  {
            transform: translate({line_offset}px, 0);
          }
          {{ id }} g.series .bar rect {
            transform: translate(-{bar_offset}px, 0);
          }
          """.replace(
            "{line_offset}", line_offset
        ).replace(
            "{bar_offset}", bar_offset
        )
        # We have to create a tempfile here because pygal only does templating
        # when loading CSS from files. Sadness. Cleanup takes place in render()
        timestamp = int(datetime.datetime.now().timestamp())
        custom_css_file = f"/tmp/pygal_custom_style_{timestamp}.css"
        with open(custom_css_file, "w") as f:
            f.write(added_css)
        self.config.css.append("file://" + custom_css_file)

    def _plot(self):
        primary_range = (self.view.box.ymin, self.view.box.ymax)
        real_order = self._order

        if self.secondary_range:
            self.view.box.ymin = self.secondary_range[0]
            self.view.box.ymax = self.secondary_range[1]
        self._order = len(self.secondary_series)
        for i, serie in enumerate(self.secondary_series, 1):
            self.bar(serie, False)

        self._order = real_order
        self.view.box.ymin = primary_range[0]
        self.view.box.ymax = primary_range[1]

        for i, serie in enumerate(self.series, 1):
            self.line(serie)

    def render(self, *args, **kwargs):
        self._fix_style()
        result = super().render(*args, **kwargs)
        # remove all the custom css files
        for css_file in self.config.css:
            if css_file.startswith("file:///tmp"):
                os.remove(css_file[7:])
        return result
