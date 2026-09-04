# Cover With Tests Prior To Refactor

This app looks pretty vibe-coded still. We've added some SDLC improvements and moved to src layout and entrypoint script to run the app. But the source code itself is still pretty raw. However, before we refactor, the test coverage is very low currently. 

## Testing Strategy
- Where possible author tests in a way that we can reuse as many as possible to validate the behavior of the app during an upcoming refactor. Which is to say that we should validate behaviors and contracts more heavily than the internal implementation of the code.
- Mock all external dependencies (weather APIs, etc.) - make no real calls during unit tests
- Mock as lightly as possible while ensuring you're testing only what you intend to and not underlying calls/dependencies
- Focus on branch coverage over line coverage if there's a trade-off to be made
- Target 100% branch coverage
- Use parametrized tests where possible to keep tests succinct and treat test cases as data rather than code
- Use pygame constructs for testing like pygame events and mock displays etc.
