"""Generated models and route list for the Bitwarden Vault Management API.

Generated from the patched OpenAPI spec by ``codegen/generate.py``.
DO NOT EDIT MANUALLY.
"""

from .models import ArchiveObjectIdPostPathParameters
from .models import AttachmentIdSchema
from .models import AttachmentPostQueryParameters
from .models import AttachmentRequestSchema
from .models import AttachmentSchema
from .models import BankAccountResponseSchema
from .models import CardResponseSchema
from .models import CollectionAccessSchema
from .models import CollectionListSchema
from .models import CollectionListSuccessSchema
from .models import CollectionResponseSchema
from .models import CollectionSchema
from .models import CollectionSuccessSchema
from .models import ConfirmOrgMemberIdPostPathParameters
from .models import ConfirmOrgMemberIdPostQueryParameters
from .models import DeviceApprovalOrganizationIdApproveAllPostPathParameters
from .models import DeviceApprovalOrganizationIdApproveRequestIdPostPathParameters
from .models import DeviceApprovalOrganizationIdDenyAllPostPathParameters
from .models import DeviceApprovalOrganizationIdDenyRequestIdPostPathParameters
from .models import DeviceApprovalOrganizationIdGetPathParameters
from .models import DeviceApprovalPropertiesSchema
from .models import DeviceApprovalRequestListSchema
from .models import DeviceApprovalRequestListSuccessSchema
from .models import DriversLicenseResponseSchema
from .models import Fido2CredentialResponseSchema
from .models import Fido2CredentialSchema
from .models import FieldResponseSchema
from .models import FieldSchema
from .models import FieldTypeSchema
from .models import FolderListSchema
from .models import FolderListSuccessSchema
from .models import FolderResponseSchema
from .models import FolderSchema
from .models import FolderSuccessSchema
from .models import GenerateGetQueryParameters
from .models import GroupSchema
from .models import IdentityResponseSchema
from .models import IdSchema
from .models import ItemBankAccountSchema
from .models import ItemCardSchema
from .models import ItemDriversLicenseSchema
from .models import ItemIdentitySchema
from .models import ItemIdSchema
from .models import ItemListSchema
from .models import ItemListSuccessSchema
from .models import ItemLoginSchema
from .models import ItemPassportSchema
from .models import ItemSchema
from .models import ItemSecureNoteSchema
from .models import ItemSshKeySchema
from .models import ItemSuccessSchema
from .models import ItemTemplateSchema
from .models import ItemTypeSchema
from .models import ListObjectCollectionsGetQueryParameters
from .models import ListObjectFoldersGetQueryParameters
from .models import ListObjectItemsGetQueryParameters
from .models import ListObjectOrganizationsGetQueryParameters
from .models import ListObjectOrgCollectionsGetQueryParameters
from .models import ListObjectOrgMembersGetQueryParameters
from .models import ListObjectSendGetQueryParameters
from .models import LockUnlockDataSchema
from .models import LockUnlockSuccessSchema
from .models import LoginResponseSchema
from .models import LoginUriResponseSchema
from .models import MatchSchema
from .models import MoveItemidOrganizationIdPostPathParameters
from .models import MoveItemRequestSchema
from .models import ObjectAttachmentIdDeletePathParameters
from .models import ObjectAttachmentIdDeleteQueryParameters
from .models import ObjectAttachmentIdGetPathParameters
from .models import ObjectAttachmentIdGetQueryParameters
from .models import ObjectCollectionIdGetPathParameters
from .models import ObjectExposedIdGetPathParameters
from .models import ObjectFolderIdDeletePathParameters
from .models import ObjectFolderIdGetPathParameters
from .models import ObjectFolderIdPutPathParameters
from .models import ObjectItemCollectionsIdGetPathParameters
from .models import ObjectItemCollectionsIdPutPathParameters
from .models import ObjectItemCollectionsIdPutRequest
from .models import ObjectItemIdDeletePathParameters
from .models import ObjectItemIdDeleteQueryParameters
from .models import ObjectItemIdGetPathParameters
from .models import ObjectItemIdPutPathParameters
from .models import ObjectNotesIdGetPathParameters
from .models import ObjectOrganizationIdGetPathParameters
from .models import ObjectOrgCollectionIdDeletePathParameters
from .models import ObjectOrgCollectionIdDeleteQueryParameters
from .models import ObjectOrgCollectionIdGetPathParameters
from .models import ObjectOrgCollectionIdGetQueryParameters
from .models import ObjectOrgCollectionIdPutPathParameters
from .models import ObjectOrgCollectionIdPutQueryParameters
from .models import ObjectOrgCollectionPostQueryParameters
from .models import ObjectPasswordIdGetPathParameters
from .models import ObjectSendIdDeletePathParameters
from .models import ObjectSendIdGetPathParameters
from .models import ObjectSendIdPutPathParameters
from .models import ObjectTemplateTypeGetPathParameters
from .models import ObjectTotpIdGetPathParameters
from .models import ObjectUriIdGetPathParameters
from .models import ObjectUsernameIdGetPathParameters
from .models import OrganizationIdSchema1
from .models import OrganizationListSchema
from .models import OrganizationListSuccessSchema
from .models import OrganizationSchema
from .models import OrganizationSuccessSchema
from .models import OrgCollectionSchema
from .models import OrgCollectionSuccessSchema
from .models import OrgMemberListSchema
from .models import OrgMemberListSuccessSchema
from .models import OrgMemberSchema
from .models import PassportResponseSchema
from .models import PasswordHistoryResponseSchema
from .models import PasswordHistorySchema
from .models import RepromptSchema
from .models import RequestIdSchema
from .models import RestoreItemIdPostPathParameters
from .models import SearchSchema
from .models import SecretStringResponseSchema
from .models import SecretStringSuccessSchema
from .models import SecureNoteResponseSchema
from .models import SendFileResponseSchema
from .models import SendIdRemovePasswordPostPathParameters
from .models import SendListGetQueryParameters
from .models import SendListSchema
from .models import SendListSuccessSchema
from .models import SendSchema
from .models import SendSuccessSchema
from .models import SendTemplateSchema
from .models import SendTextResponseSchema
from .models import SendTextSchema
from .models import SendTypeSchema
from .models import SshKeyResponseSchema
from .models import StatusDataSchema
from .models import StatusSchema
from .models import StringResponseSchema
from .models import StringSuccessSchema
from .models import SuccessSchema
from .models import SyncMessageSchema
from .models import SyncMessageSuccessSchema
from .models import SyncPostQueryParameters
from .models import TemplateResponseSchema
from .models import TemplateSchema
from .models import TemplateStatusSchema
from .models import TemplateSuccessSchema
from .models import TypeSchema
from .models import UnlockPostRequestSchema
from .models import UrisSchema
from .routes import Parameter
from .routes import Route
from .routes import ROUTES

__all__ = [
  "ItemTypeSchema", "RepromptSchema", "ItemSecureNoteSchema", "ItemCardSchema", "ItemIdentitySchema", "MatchSchema", "UrisSchema",
  "FieldTypeSchema", "FieldSchema", "FolderSchema", "SendTypeSchema", "SendTextSchema", "GroupSchema", "TemplateStatusSchema",
  "TemplateSchema", "StatusDataSchema", "StatusSchema", "LockUnlockDataSchema", "LockUnlockSuccessSchema",
  "DeviceApprovalPropertiesSchema", "PasswordHistorySchema", "Fido2CredentialSchema", "ItemSshKeySchema", "ItemBankAccountSchema",
  "ItemDriversLicenseSchema", "ItemPassportSchema", "AttachmentSchema", "PasswordHistoryResponseSchema",
  "Fido2CredentialResponseSchema", "LoginUriResponseSchema", "FieldResponseSchema", "LoginResponseSchema",
  "SecureNoteResponseSchema", "CardResponseSchema", "IdentityResponseSchema", "SshKeyResponseSchema", "BankAccountResponseSchema",
  "DriversLicenseResponseSchema", "PassportResponseSchema", "ItemSchema", "FolderResponseSchema", "SendTextResponseSchema",
  "SendFileResponseSchema", "SendSchema", "OrganizationSchema", "CollectionResponseSchema", "CollectionAccessSchema",
  "OrgCollectionSchema", "OrgMemberSchema", "StringResponseSchema", "SecretStringResponseSchema", "TemplateResponseSchema",
  "SyncMessageSchema", "ItemListSchema", "FolderListSchema", "SendListSchema", "OrganizationListSchema", "CollectionListSchema",
  "OrgMemberListSchema", "SuccessSchema", "ItemSuccessSchema", "ItemListSuccessSchema", "StringSuccessSchema",
  "SecretStringSuccessSchema", "FolderSuccessSchema", "FolderListSuccessSchema", "SendSuccessSchema", "SendListSuccessSchema",
  "OrganizationSuccessSchema", "OrganizationListSuccessSchema", "CollectionSuccessSchema", "CollectionListSuccessSchema",
  "OrgCollectionSuccessSchema", "OrgMemberListSuccessSchema", "TemplateSuccessSchema", "SyncMessageSuccessSchema", "IdSchema",
  "ObjectItemIdPutPathParameters", "ObjectItemIdGetPathParameters", "ObjectItemIdDeletePathParameters",
  "ObjectItemIdDeleteQueryParameters", "ObjectItemCollectionsIdGetPathParameters", "ObjectItemCollectionsIdPutPathParameters",
  "RestoreItemIdPostPathParameters", "ArchiveObjectIdPostPathParameters", "OrganizationIdSchema1", "SearchSchema",
  "ListObjectItemsGetQueryParameters", "ItemIdSchema", "AttachmentPostQueryParameters", "AttachmentIdSchema",
  "ObjectAttachmentIdGetPathParameters", "ObjectAttachmentIdGetQueryParameters", "ObjectAttachmentIdDeletePathParameters",
  "ObjectAttachmentIdDeleteQueryParameters", "ObjectUsernameIdGetPathParameters", "ObjectPasswordIdGetPathParameters",
  "ObjectUriIdGetPathParameters", "ObjectTotpIdGetPathParameters", "ObjectNotesIdGetPathParameters",
  "ObjectExposedIdGetPathParameters", "ObjectFolderIdPutPathParameters", "ObjectFolderIdGetPathParameters",
  "ObjectFolderIdDeletePathParameters", "ListObjectFoldersGetQueryParameters", "ObjectSendIdPutPathParameters",
  "ObjectSendIdGetPathParameters", "ObjectSendIdDeletePathParameters", "ListObjectSendGetQueryParameters",
  "SendListGetQueryParameters", "SendIdRemovePasswordPostPathParameters", "MoveItemidOrganizationIdPostPathParameters",
  "ObjectOrgCollectionPostQueryParameters", "ObjectOrgCollectionIdPutPathParameters", "ObjectOrgCollectionIdPutQueryParameters",
  "ObjectOrgCollectionIdGetPathParameters", "ObjectOrgCollectionIdGetQueryParameters", "ObjectOrgCollectionIdDeletePathParameters",
  "ObjectOrgCollectionIdDeleteQueryParameters", "ListObjectOrgCollectionsGetQueryParameters",
  "ListObjectCollectionsGetQueryParameters", "ListObjectOrganizationsGetQueryParameters", "ListObjectOrgMembersGetQueryParameters",
  "ObjectCollectionIdGetPathParameters", "ObjectOrganizationIdGetPathParameters", "ConfirmOrgMemberIdPostPathParameters",
  "ConfirmOrgMemberIdPostQueryParameters", "DeviceApprovalOrganizationIdGetPathParameters", "RequestIdSchema",
  "DeviceApprovalOrganizationIdApproveRequestIdPostPathParameters", "DeviceApprovalOrganizationIdApproveAllPostPathParameters",
  "DeviceApprovalOrganizationIdDenyRequestIdPostPathParameters", "DeviceApprovalOrganizationIdDenyAllPostPathParameters",
  "SyncPostQueryParameters", "GenerateGetQueryParameters", "TypeSchema", "ObjectTemplateTypeGetPathParameters",
  "UnlockPostRequestSchema", "ObjectItemCollectionsIdPutRequest", "AttachmentRequestSchema", "MoveItemRequestSchema",
  "ItemLoginSchema", "SendTemplateSchema", "CollectionSchema", "DeviceApprovalRequestListSchema",
  "DeviceApprovalRequestListSuccessSchema", "ItemTemplateSchema", "Parameter", "Route", "ROUTES"
]
