# Theming Update

I want to fully implement a theme-ing system. While I want it to be full-featured I am targeting a weatherstar 3000 theme as the only other concrete implementation. The Theme should change the look and feel of a given screen based on theme name.

We:
- Should not duplicate screens to implement theming
- Should make a screen have some sort of way to respond to theme name
- Should have a way of defining themes

Discuss:
I'm a little worried about the size of the config file. It's already large and defining theme seems like it will push it over the edge.

We might consider having a separate theme config file. Or maybe even theme config file per theme where anything named like `<theme_name>.theme.toml` or something like that defines themes. And active theme is specified in the main config file?