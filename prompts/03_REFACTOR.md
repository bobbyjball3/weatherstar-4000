# Big Bang Refactor

I want to refactor this entire application. I like the functionality it has now, but the code and the configuration system. I want the existing screens, their content, etc. preserved in the new code, but implemented in the new method. 

I want to add the following abstractions:
- Screen: the top-most container for content to be displayed. I think these are currently "Displays"
- Components: objects, text, tables, animations, etc. that can be rendered on the Screen
- An abstraction for local media sources like fonts, images, gifs, music, etc. This abstraction should be able to be added to the Screen and the Component optionally to decorate the component or screen with media
- Datasource: abstract data source from which a component can retrieve data. Like external APIs
  - Datasource should support configuration of authentication. Any settings for authentication are treated as sensitive and masked in any call to repr, str, etc. so that they are not logged. 
- Sequence: A sequence of Screens with optional pause time specified for each slide as well as a global pause setting if not specified.

General requirements:
- I want each of these abstractions to be a plugin system so that you can compose new screens and reference them in a Sequence. 
- Each of the Screen, Component, Media, and Datasource abstractions should be able to declare certain attributes on their implementation as "configurable" and a default value and that should automatically register them for inclusion in a configuration scope in the global configuration file (e.g. toml file).
- If any abstraction in the plugin system (above) is referenced in the sequence the required configuration must be present in the configuration file otherwise an InvalidConfiguration exception should be thrown with an example for the missing configuration. 
- Config file is a required if no other configuration arguments are specified
- Based on the declared Sequence (a global required argument specifying which sequence to execute). Should be a required argument/envvar/config file param. Should be able to generate a skeleton configuration file for the sequence.  
- Logging should be structured and ANSII color coded by attributes like severity. 
  - logging should by default just go to stdout/stderr unless a log file location is specified. In which case logging should be directed to the specified file as well as stdout/stderr unless a logging option to disable stdout/stderr output is specified.
