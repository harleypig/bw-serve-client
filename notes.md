# Hey there, welcome to the Vault Management API module!

We're here to guide you through using the Bitwarden CLI's `bw serve` command to access the Vault Management API. If you're after the Organization Management API, you might want to check out [this resource](https://bitwarden.com/help/api/) instead. For all the nitty-gritty details on the API we're using, take a peek at the [official documentation](https://bitwarden.com/help/vault-management-api/).

Before diving in, you'll need to [download and install](https://bitwarden.com/download/#downloads-command-line-interface) the Bitwarden CLI on your own. Now, let's talk about what this module doesn't do. We're not going to support email and master password login to start with. It's not the most secure method, and we'd need a pretty compelling argument to consider it. Also, we're skipping SSO support for the time being. But don't worry, we've got you covered with the API key method, which is secure and straightforward. You can get the scoop on [using an API key here](https://bitwarden.com/help/cli/#using-an-api-key).

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
