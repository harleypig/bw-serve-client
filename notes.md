# move various requirements.txt files to poetry toml file
- `requirements.txt`: Used for pip requirements, not needed as Poetry manages dependencies in `pyproject.toml`.
- `test-requirements.txt`: Used for pip requirements for testing, not needed as Poetry can handle test dependencies in `pyproject.toml`.
- `doc-requirements.txt`: Requirements for documentation, not needed as Poetry can handle documentation dependencies in `pyproject.toml`.

# Can poetry handle version management in git and python files too?
- `.bumpversion.toml`: Configuration for version bumping, not needed as Poetry can handle version management.
- `bump_version`: Script for version bumping, not needed as Poetry can handle version management.

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

## TODO?

# Run generate.api |& tee gen.log

```
##############################################################################
# XXX: Do something about this?
#
# [main] INFO  o.o.codegen.InlineModelResolver - Inline schema created as _attachment_post_request. To have complete control of the model name, set the `title` field or use the modelNameMapping option (e.g. --model-name-mappings _attachment_post_request=NewModel,ModelA=NewModelA in CLI) or inlineSchemaNameMapping option (--inline-schema-name-mappings _attachment_post_request=NewModel,ModelA=NewModelA in CLI).
#
# --inline-schema-name-mappings _attachment_post_request=NewModel,ModelA=NewModelA
# --inline-schema-name-mappings lockunlock_success_data=NewModel,ModelA=NewModelA
# --inline-schema-name-mappings status_data=NewModel,ModelA=NewModelA
# --inline-schema-name-mappings status_data_template=NewModel,ModelA=NewModelA
# --inline-schema-name-mappings _unlock_post_request=NewModel,ModelA=NewModelA
#
# OR
#
# --model-name-mappings _attachment_post_request=NewModel,ModelA=NewModelA
# --model-name-mappings lockunlock_success_data=NewModel,ModelA=NewModelA
# --model-name-mappings status_data=NewModel,ModelA=NewModelA
# --model-name-mappings status_data_template=NewModel,ModelA=NewModelA
# --model-name-mappings _unlock_post_request=NewModel,ModelA=NewModelA

##############################################################################
# XXX: Do I need to fix this? What is the unknown type?
#
#[main] INFO  o.o.codegen.utils.URLPathUtils - 'host' (OAS 2.0) or 'servers' (OAS 3.0) not defined in the spec. Default to [http://localhost] for server URL [http://localhost/]
#
#[main] WARN  o.o.codegen.DefaultCodegen - Unknown type found in the schema: int. To map it, please use the schema mapping option (e.g. --schema-mappings in CLI)

##############################################################################
# XXX: Do I need to worry about these?

# [main] WARN  o.o.c.l.AbstractPythonPydanticV1Codegen - Failed to lookup model in createImportMapOfSet Int
# [main] ERROR o.o.c.l.AbstractPythonPydanticV1Codegen - Failed to look up Int from the imports (map of set) of models.
# [main] ERROR o.o.c.l.AbstractPythonPydanticV1Codegen - Failed to look up Int from the imports (map of set) of models.
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /attachment. Renamed to auto-generated operationId: attachmentPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /confirm/org-member/{id}. Renamed to auto-generated operationId: confirmOrgMemberIdPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /generate. Renamed to auto-generated operationId: generateGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/collections. Renamed to auto-generated operationId: listObjectCollectionsGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/folders. Renamed to auto-generated operationId: listObjectFoldersGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/items. Renamed to auto-generated operationId: listObjectItemsGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/org-collections. Renamed to auto-generated operationId: listObjectOrgCollectionsGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/org-members. Renamed to auto-generated operationId: listObjectOrgMembersGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/organizations. Renamed to auto-generated operationId: listObjectOrganizationsGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /list/object/send. Renamed to auto-generated operationId: listObjectSendGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /lock. Renamed to auto-generated operationId: lockPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/attachment/{id}. Renamed to auto-generated operationId: objectAttachmentIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: delete /object/attachment/{id}. Renamed to auto-generated operationId: objectAttachmentIdDelete
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/exposed/{id}. Renamed to auto-generated operationId: objectExposedIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/fingerprint/me. Renamed to auto-generated operationId: objectFingerprintMeGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /object/folder. Renamed to auto-generated operationId: objectFolderPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/folder/{id}. Renamed to auto-generated operationId: objectFolderIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: put /object/folder/{id}. Renamed to auto-generated operationId: objectFolderIdPut
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: delete /object/folder/{id}. Renamed to auto-generated operationId: objectFolderIdDelete
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /object/item. Renamed to auto-generated operationId: objectItemPost
# [main] WARN  o.o.codegen.DefaultCodegen - Unknown type found in the schema: int. To map it, please use the schema mapping option (e.g. --schema-mappings in CLI)
# [main] WARN  o.o.codegen.DefaultCodegen - Unknown type found in the schema: int. To map it, please use the schema mapping option (e.g. --schema-mappings in CLI)
# [main] WARN  o.o.codegen.DefaultCodegen - Unknown type found in the schema: int. To map it, please use the schema mapping option (e.g. --schema-mappings in CLI)
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/item/{id}. Renamed to auto-generated operationId: objectItemIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: put /object/item/{id}. Renamed to auto-generated operationId: objectItemIdPut
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: delete /object/item/{id}. Renamed to auto-generated operationId: objectItemIdDelete
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/notes/{id}. Renamed to auto-generated operationId: objectNotesIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /object/org-collection. Renamed to auto-generated operationId: objectOrgCollectionPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/org-collection/{id}. Renamed to auto-generated operationId: objectOrgCollectionIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: put /object/org-collection/{id}. Renamed to auto-generated operationId: objectOrgCollectionIdPut
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: delete /object/org-collection/{id}. Renamed to auto-generated operationId: objectOrgCollectionIdDelete
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/password/{id}. Renamed to auto-generated operationId: objectPasswordIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /object/send. Renamed to auto-generated operationId: objectSendPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/send/{id}. Renamed to auto-generated operationId: objectSendIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: put /object/send/{id}. Renamed to auto-generated operationId: objectSendIdPut
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: delete /object/send/{id}. Renamed to auto-generated operationId: objectSendIdDelete
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/template/{type}. Renamed to auto-generated operationId: objectTemplateTypeGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/totp/{id}. Renamed to auto-generated operationId: objectTotpIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/uri/{id}. Renamed to auto-generated operationId: objectUriIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /object/username/{id}. Renamed to auto-generated operationId: objectUsernameIdGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /restore/item/{id}. Renamed to auto-generated operationId: restoreItemIdPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /send/{id}/remove-password. Renamed to auto-generated operationId: sendIdRemovePasswordPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: get /status. Renamed to auto-generated operationId: statusGet
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /sync. Renamed to auto-generated operationId: syncPost
# [main] WARN  o.o.codegen.DefaultCodegen - Empty operationId found for path: post /unlock. Renamed to auto-generated operationId: unlockPost
```
