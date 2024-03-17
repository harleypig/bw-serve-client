# Notes

## API Source

[API](https://bitwarden.com/help/vault-management-api/) source

## Bitwarden CLI Docs

[CLI](https://bitwarden.com/help/cli/)

## Expectations

* User must [download and
    install](https://bitwarden.com/download/#downloads-command-line-interface)
    application themselves.
* This module won't be supporting email and master password login, at least
    initially. And it's a bad idea, so would require some discussion to change
    my mind.
* This module won't be supporting SSO initially ... I don't use it and the
    docs suggest you can still use an api key.
* That leaves [using an api
    key](https://bitwarden.com/help/cli/#using-an-api-key).

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
