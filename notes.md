# Bitwarden CLI Vault Management API

This module supports the [Bitwarden CLI Vault Management
API](https://bitwarden.com/help/vault-management-api/), available via
Bitwarden CLI's `bw serve` command.

If you're looking for Bitwarden's public api (for organizational tools and
stuff) that API is [here](https://bitwarden.com/help/api/)

You'll need to [download and
install](https://bitwarden.com/help/cli/#download-and-install) the [Bitwarden
CLI](https://bitwarden.com/download/#downloads-command-line-interface) on your
own.

Please note that this module won't be supporting email and master password
login to start with. It's not the most secure method, but pull requests are
welcome. Also, SSO support is low on the todo list, as the author doesn't use
it.


got you covered with the API key method,
which is secure and straightforward. You can get the scoop on [using an API
key here](https://bitwarden.com/help/cli/#using-an-api-key).

## Steps

* Probably want to support this.
  - bw config server (see help)

* Check status
* - unauthenticated, need to login --apikey
* - locked, need to unlock
* - unlocked, nothing needs to be done

* Is there an api options for sync?
* bw serve

### login --apikey

[docs](https://bitwarden.com/help/cli/#using-an-api-key)

Environment variables (both required):
* BW_CLIENTID
* BW_CLIENTSECRET

### unlock

[docs](https://bitwarden.com/help/cli/#unlock)

* --passwordenv <ENVIRONMENT_VARIABLE>
* --passwordfile /path/to/file
* prompt for password

Capture BW_SESSION and set it.

In bash, only bash scripts can be sourced, so we can't set the environment
variable outside of the script. Provide an option for the user to be to do
something like the following.
```
BW_SESSION="$(bw-serve-client unlock [--passwordenv|--passwordfile|prompt])"
```
So they aren't stomping all over themselves when using both the command line
and this module.

There is a --session option for each command, but I'm not supporting that.
