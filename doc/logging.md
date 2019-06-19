# How does Happy test log work

## Types of Happy logs

  * Debug logs - Logs related to Happy's role as test coordinator and orchestrator, where it facilitates the activities of virtual device nodes.

  * Device logs - Logs related to software such as OpenWeave running on individual virtual device nodes within a Happy test network. OpenWeave is one of the software example, device logs may have OpenWeave logs.

## Where Happy logs are stored

  * If the `HAPPY_LOG_DIR` environment variable exists, Happy uses the `HAPPY_LOG_DIR` value as log folder location to store Happy test logs.

  * If the `HAPPY_LOG_DIR` environment variable doesn't exist, Happy uses the `default_happy_log_dir` value from [happy/conf/main_config.json](https://github.com/openweave/happy/blob/master/happy/conf/main_config.json) as the default log folder location to store Happy test logs. The default value of `default_happy_log_dir` is `/tmp`.

## How to set `HAPPY_LOG_DIR`

  There are multiple ways to see the `HAPPY_LOG_DIR` environment variable::
  * If your project is being built with GNU autotools and you are running functional and unit tests with Happy with the DejaGnu test framework, then you might add `HAPPY_LOG_DIR=<dir value>` to TESTS_ENVIRONMENT in your Makefile.am or Makefile.in.
  * Add `HAPPY_LOG_DIR=<dir value>` to .bashrc and source it before you run the test script.
