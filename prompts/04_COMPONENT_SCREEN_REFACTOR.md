# Component/Screen Concept Refactor

Looking over the code, Component construct seems a bit messy and spread out with some components defined in the root of the project and some in the components subpackage. I also notice that there are things I see written directly into implemented Screens that could be components. Let's talk through cleaning up that abstraction. 

Objectives:
- Move more implementation into components rather than Screen
- Clean up relationship between Screen and Component

Changes:
- Screens currently have a lot of code in them that looks like building things that should be Components
- I really expect Screens to largely just be composed using components with the only real logic in Screens being where to place components and how/if to animate them.
- For things like news historical screens that have a scrolling nature to them, I'd almost deligate the scrolling behavior to the component as a cleaner implementation
- There are components defined in @src/weatherstar_4000/components/header.py
  - The filename is confusing as it contains multiple components. 
  - Like Screens, each component should be it's own file I think. 
- I see some consistent helper functions being defined outside the Screen implementations (e.g. _font, _color, etc.). If they're pretty consistent, these should become part of the interface I think. And if possible, perhaps they become implementations on the interface and not just interfaces.
