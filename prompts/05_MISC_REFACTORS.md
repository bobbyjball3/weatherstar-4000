# Misc. Refactors

I want to refactor various parts of the app where the code is messy or overly complex.

# Changes
- renderer.py:_icon_for_token - This is some serious spaghetti code. Some ideas for refactor to talk through:
  - Turn the decision tree into a dict[str|list[dict]] so that you can capture the decision tree and then use some conditional/recursive logic to continue to solve for the icon
  - ... honestly not sure of another way here.
- I see a lot of guard code like `thing.get("attr", None) or {}` this wreaks to me of bad data contracts between the producer and consumer of the data. Where at all possible have the producer of the data (mostly Datasources) always produce a suitable value (either data or empty but never missing entirely etc.)
- I see a good deal of things like `if ds is not None:` for things like this, I actually think it's more desirable to just crash. Because it simply means they're referencing a datasource that doesn't exist. There's nothing code can reasonably do at that point and I'd rather crash than run and have "no data present" which is more difficult to debug
- I see a lot of raw Dicts (see behavior immediately above). I think we should have some stronger internal data contracts
- Datasources should own their public interface data contract, and that data contract does not need to match the data contract of the underlying API etc. The public interface data contract should present the data in a way that's useful in the context of this application.
- The video, logging, and location comments being hardcoded dicts seems to indcate to me we've broken out of the nice configuration system I devised. Let's not do that - those should be configurable in the same way as the rest of the app.
  - In fact, if we had a `Configuration` object that had all config sections/elements from registered fields, you should be able to loop over that in it's entirety and simplify the rendering code.
- Whenever a resource initializes, it should log the effective configuration for that resource (be it component, datasource, screen, etc.) for debugging purposes

# Things to discuss
- I still see a lot of code in the `compose` method of screens. More than I'd like, and I wonder if some delegation of concerns would be useful here. If there was a consistent data contract with datasources (maybe an envelope that is fixed and a `data` element that contains the data), we could provide metadata around coloration, style, etc.
  - This would delegate a lot of the style code (which is a lot of the spaghetti I see) to datasources themselves. That protects components using the datasource from needing to deeply understand the shape of the data and focus more on placement/composition of the screen.
- I think we've biased towards not creating a component if there's only one concrete example of it's usage (for instance current conditions page). But I think that's leading to mixing concerns. I think we should potentially define a rule here
  - This also opens up the posibility of splitting some concerns between datasoruces and the components that use them around styling - though I still think Datasources (who's job is to deeply understand the data they're retrieving and interacting with) should still be mostly responsible for style and format of the data. 
- I'm going to be doing a major feature coming up called themes. There's a themes.py, but it's basically useless. General theming (consistent background, color schemes, etc.) is desired, but the ultimate objective is to implement a way to present weatherstation3000 and 4000 in the same app driven off of configuration. I'm interested in understanding if there's anything we can front-load to make that implementation easier (though this is already a fairly large refactor, so perhaps an intermediary refactor would be good instead of lumping them together now)
  - I'm currently torn on implementation here. One way would be to write the screens, components, etc. in a way that flipping the theme name causes them to alter their appearance. This feels like the way, but is a bit complex.
  - Another way would be to require completely parallel implementations of screens, components, etc. for each theme. This feels very duplicative
