
Status:
Tags: [[GenAI]] [[AI Agents]] [[LinkedIn Agents]]

# LinkedIn Agents
[[API Development]]

There are two types of Authorization Flows available:

- [**Member Authorization (3-legged OAuth)**](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication?toc=%2Flinkedin%2Fmarketing%2Ftoc.json&bc=%2Flinkedin%2Fbreadcrumb%2Ftoc.json&view=li-lms-2026-02#member-authorization-3-legged-oauth-flow)
- [**Application Authorization (2-legged OAuth)**](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication?toc=%2Flinkedin%2Fmarketing%2Ftoc.json&bc=%2Flinkedin%2Fbreadcrumb%2Ftoc.json&view=li-lms-2026-02#application-authorization-2-legged-oauth-client-credential-flow)
- [[Build an Ad Campaign]]
Marketing campaigns are structured like this:

1. Ad account
    1. Campaign group
        1. Campaign
        2. Objective
        3. Creative
        4. Launch/manage

# Advertising
The Advertising API enables developers to manage LinkedIn's campaign management platform on behalf of clients through APIs. These APIs provide all features available in LinkedIn Campaign Manager, including creation and management of ad accounts, campaign groups, campaigns, creatives, ad types, and analytics.

With access to the Advertising API program, developers can create and manage Ad Accounts entirely through APIs without depending on the LinkedIn Campaign Manager UI. API calls succeed only when made with correct scopes/permissions assigned to the app after the vetting process. Once the developer application has the required permissions, all Advertising Account features can be accessed by passing identifiers from API responses in the hierarchy.

## Core Components
### Ad Accounts

LinkedIn enables you to create Ad Accounts for your organization's advertising campaigns. Each Ad Account supports:

- Maximum 5,000 campaigns
- Maximum 15,000 creatives
- Requires Enterprise or Business Ad Account with one authenticated user as account administrator
### Account Users

The [Ad Account Users](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02) enables advertisers to manage ad account user access. Ad account users are members who have ad account permissions in LinkedIn Campaign Manager. Partners can control user roles for granular access management.
### Campaign Groups

[Campaign groups](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02) help advertisers manage status, budget, and performance across multiple related campaigns. Key features:

- Automatically created when an Ad Account is created
- Can contain various campaign types
- No limit on campaign groups per advertiser account
- Limits: 5,000 campaigns per advertiser account, 2,000 campaigns per non-default campaign group
### Campaigns

[Campaigns](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02) define ad schedules and budgets (daily/total). Campaigns can:

- Be bound to a specific start and end date or run continuously until the budget is spent
- Target specific member audiences based on job title, function, seniority, and other criteria
### Creatives

The Creatives API contains data and information for visually rendering ads. Available ad creative types:

- **Video Ads**: Next-generation Sponsored Content for engaging business decision-makers on LinkedIn's mobile and desktop feeds
- **Message Ads**: Messages delivered to LinkedIn members' InMail inboxes
- **Job Ads**: Personalized ads targeting top talent to encourage relevant candidates to apply
- **Text Ads**: Text-based advertising format
- **Image Ads**: [Single Image Ads](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/image-ads-integrations?view=li-lms-2026-02) are Sponsored Content posts appearing in LinkedIn feeds, delivering targeted messages beyond your organization's LinkedIn Page
- **Follower Ads**: [Follower Ads](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/follower-ads?view=li-lms-2026-02) promote your LinkedIn Page or Showcase Page to encourage follows
- **Carousel Ads**: Sponsored Content format displaying multiple images in succession
- **Article Ads**: Sponsored Content posts appearing in LinkedIn feeds for targeted messaging
- **Spotlight Ads**: [Spotlight Ads](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/spotlight-ads?view=li-lms-2026-02) showcase products, services, events, or content, directing users to your chosen website or landing page
- **Conversation Ads**: LinkedIn ad format delivering pre-determined messages to targeted members' inboxes, providing chat-like experiences

### Analytics

LinkedIn Reporting APIs provide key performance insights including:

- Clicks, impressions, and ad spend
- Professional demographics metrics by demographic values
- Data available at account, campaign, and creative levels

These insights help users optimize their LinkedIn ads experience and ensure effective campaign performance.

# Cursor Based Pagination For Search APIs
From 202401 version and above, we have moved from index based pagination to cursor based pagination for our search APIs for the following endpoints:

- adAccounts
- adCampaignGroups
- adCampaigns
- adCreatives

API calls that return a large number of entities are broken up into multiple pages of results. You might need to make multiple API calls with slightly varied paging parameters to iteratively collect all the data you're trying to gather.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/cursor-based-pagination?view=li-lms-2026-02#parameters)

## Parameters

|Name|Description|Default|
|---|---|---|
|pageSize|Specifies the number of entities to be returned. The default is 100.|100|
|pageToken|Unique key used to fetch the next set of entities. `nextPageToken` is returned in metadata field of the search response. This should be passed in `pageToken` query parameter in the request to get the next page of results.||

To paginate through results, begin with a `pageSize` value of N and no pageToken. To get the next set of results, set `pageToken` value to the `nextPageToken` returned in the previous response, while the `pageSize` value stays the same.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/cursor-based-pagination?view=li-lms-2026-02#sample-request)

## Sample Request

HTTP

```
GET https://api.linkedin.com/v2/{service}?pageSize=10
```

---

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/cursor-based-pagination?view=li-lms-2026-02#sample-response)

#### Sample Response

JSON

```
{
  "metadata": {
    "nextPageToken": "DgGerr1iVQreCJVjZDOW_grcp63nueBDipsS4DJpvJo"
  },
  "elements": [
    {"Result #0"},
    {"Result #1"},
    {"Result #2"},
    {"Result #3"},
    {"Result #4"},
    {"Result #5"},
    {"Result #6"},
    {"Result #7"},
    {"Result #8"},
    {"Result #9"}
  ]
}
```

API Call to get the next set of results would use the `nextPageToken` returned in the response above.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/cursor-based-pagination?view=li-lms-2026-02#sample-request-1)

#### Sample Request

HTTP

```
GET https://api.linkedin.com/v2/{service}?pageSize=10&pageToken=DgGerr1iVQreCJVjZDOW_grcp63nueBDipsS4DJpvJo
```

---

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/cursor-based-pagination?view=li-lms-2026-02#end-of-the-dataset)

### End of the Dataset

When the response doesn't contain a `nextPageToken`, it indicates that you have reached the end of the dataset.


# # Ad Accounts
## Permissions

two conditions for successful Ad Account Users API calls:

- Scope permission accessibility for:
    
    - `rw_ads` (read/write).
    - `r_ads` (read-only)
- The ad account user assigning permission holding one of the following ad account roles:
    
    - `ACCOUNT_BILLING_ADMIN`
    - `ACCOUNT_MANAGER`
    - `CAMPAIGN_MANAGER`
    - `CREATIVE_MANAGER`
    - `VIEWER` (read-only, even with `rw_ads` scope)

For more information on Ad Account roles and permissions, refer to the following:

### Pagination for non-search APIs

The `adAccountsV2` API implements pagination using the `start` and `count` parameters, where the max `count`=1000.

A `400 Bad Request` notification is returned if:

- `count` value > 1000, or
- Response elements > 100 **and** the request doesn't have pagination request parameters.

| Field Name                     | Type                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Required | Additional Info Field |
| ------------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------- |
| currency                       | string, default="USD"    | The 3 character standard currency code such as USD for United States Dollar. Refer to the [list of supported currencies](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/supported-currencies?view=li-lms-2026-02) for the full list.  <br>**Note:** Advertisers selecting Brazilian Real (BRL) as a currency see their account budget, advertising bids, and spend in BRL, but their account is billed in USD. We recommend communicating this to stakeholders in your application if they opt for BRL. [Learn more](https://www.linkedin.com/help/linkedin/answer/41250)                                                                                                                                                                                                            | False    | False                 |
| id                             | long                     | Unique internal ID representing the account                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | False    | False                 |
| name                           | string                   | A label for the account                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | True     | False                 |
| notifiedOnCampaignOptimization | boolean, default="false" | Indicates if the campaign contact is notified about campaign optimization opportunities                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | False    | False                 |
| notifiedOnCreativeApproval     | boolean, default="false" | Indicates if the creative contact is notified when a creative has been reviewed and approved                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | False    | False                 |
| notifiedOnCreativeRejection    | boolean, default="false" | Indicates if the creative contact is notified when a creative has been rejected due to content                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | False    | False                 |
| notifiedOnEndOfCampaign        | boolean, default="false" | Indicates if the campaign contact is notified when an associated campaign has been completed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | False    | False                 |
| notifiedOnNewFeaturesEnabled   | boolean, default="false" | Indicates if the account owner is notified about new Campaign Manager features                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | False    | False                 |
| reference                      | optional URN             | The entity on whose behalf the account is advertised. Must either be in the format urn:li:person:{id} or urn:li:organization:{id}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | False    | False                 |
| referenceInfo                  | Union                    | Information about the entity associated with the reference. If the entity is an organization, an [Organizationinfo](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-accounts?view=li-lms-2026-02&tabs=http#organizationinfo) object is returned. If the entity is a person, a [Personinfo](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-accounts?view=li-lms-2026-02&tabs=http#personinfo) object is returned. For all other entity types an empty record will be returned. This is a read only field. Please refer to [Additional Info Fields](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02) to learn how to access this field. | False    | True                  |
| servingStatuses                | string[], default="[]"   | An array of enums with information about the account's system serving statuses. If an account is eligible for serving, then the array has a single element:- RUNNABLE Otherwise, the array contains one or more reasons why the account is not servable:<br>- STOPPED<br>- BILLING_HOLD<br>- ACCOUNT_TOTAL_BUDGET_HOLD<br>- ACCOUNT_END_DATE_HOLD<br>- RESTRICTED_HOLD<br>- INTERNAL_HOLD                                                                                                                                                                                                                                                                                                                                                                                                                 | False    | False                 |
| status                         | string, default="ACTIVE" | - ACTIVE - Account is active; this is the default state<br>- CANCELED - Account has been permanently canceled<br>- DRAFT - Account is in draft status, meaning it's not yet fully set up and it's not serving<br>- PENDING_DELETION - Denotes that the account has been requested to be deleted that's currently pending<br>- REMOVED - Denotes that the account was deleted, but must remain fetchable due to the existence of performance data.                                                                                                                                                                                                                                                                                                                                                         | False    | False                 |
| type                           | string                   | - BUSINESS – This is the only value allowed when creating accounts through the API.<br>- ENTERPRISE – This value can't be used to create accounts through the API and is reserved for accounts created by LinkedIn's internal ad operations systems.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | True     | False                 |
| test                           | boolean, default="false" | Flag showing whether this account is marked as a test account. An account can be marked as test only during creation. This is an immutable field.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | False    | False                 |




### OrganizationInfo

| Field Name    | Type                                                                                                                                    | Description                                                                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| id            | long                                                                                                                                    | Unique ID representing the organization.                                                                                                            |
| name          | [MultiLocaleString](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02#multilocalestring) | Name of the organization.                                                                                                                           |
| vanityName    | string                                                                                                                                  | Name of the organization present in the URLs.                                                                                                       |
| localizedName | string                                                                                                                                  | Locale specific name of the organization.                                                                                                           |
| logo          | [CroppedImage](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02#croppedimage)           | The organization’s logo. The sizes may vary greatly, i.e., 50x50, 100x60, 400x400, so clients should handle the given height and width accordingly. |
|               |                                                                                                                                         |                                                                                                                                                     |


## Fetch Ad Account
Individual Ad Accounts can be fetched with the following endpoint taking in an `adAccount` ID.
HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountID}
```

{ "test": false, "changeAuditStamps": { "created": { "actor": "urn:li:person:fGcyYDdglZ", "time": 1449768717000 }, "lastModified": { "actor": "urn:li:unknown:0", "time": 1477941718075 } }, "currency": "USD", "id": 123456, "name": "Company A", "notifiedOnCampaignOptimization": true, "notifiedOnCreativeApproval": true, "notifiedOnCreativeRejection": true, "notifiedOnEndOfCampaign": true, "reference": "urn:li:organization:2414183", "servingStatuses": [ "RUNNABLE" ], "status": "ACTIVE", "type": "BUSINESS", "version": { "versionTag": "10" } }

# Ad Account Users API
two conditions for successful Ad Account Users API calls:

- Scope permission accessibility for:
- `rw_ads` (read/write)
    
- `r_ads` (read-only)
    
- The Ad Account user assigning permission holding one of the following Ad Account roles:
    
    - `ACCOUNT_BILLING_ADMIN`
    - `ACCOUNT_MANAGER`
    - `CAMPAIGN_MANAGER`
    - `CREATIVE_MANAGER`
    - `VIEWER` (read-only, even with `rw_ads` scope)

## Ad Account User Role Definitions

The following table describes in detail what each role provides:

| Control Name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Description                                                                                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| VIEWER                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | View campaign data and reports for the account. No ability to create or edit campaigns or ads.                                                                                                                       |
| CREATIVE_MANAGER                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | View campaign data and reports for the account. Ability to create and edit ads.                                                                                                                                      |
| CAMPAIGN_MANAGER                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | View campaign data and reports for the account. Ability to create and edit campaigns and ads.                                                                                                                        |
| ACCOUNT_MANAGER                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | View campaign data and reports for the account. Ability to create and edit campaigns and ads. Edit account data and manage user access for the account.                                                              |
| ## Schema<br><br>\|Field Name\|Type\|Description\|<br>\|---\|---\|---\|<br>\|account\|SponsoredAccountUrn\|Associated advertiser account URN\|<br>\|createdAt\|long\|Timestamp corresponding to the creation of this record. Number of milliseconds since midnight, January 1, 1970 UTC.\|<br>\|lastModifiedAt\|long\|Timestamp corresponding to the last modification of the record. If no modification has happened since creation, `lastModifiedAt` should be the same as created. Number of milliseconds since midnight, January 1, 1970 UTC.\|<br>\|role\|AccountUserRole\|Enum of user's role in this account. See the Account User Roles table above for the possible values.\|<br>\|user\|PersonUrn\|Associated user URN for your developer app in the format `urn:li:person:{PersonID}`. Retrieve PersonID by sending a `GET /me` request for the authenticated member from your developer application.\|ACCOUNT_BILLING_ADMIN | View campaign data and reports for the account. Ability to create and edit campaigns and ads. Edit account data and manage user access for the account. Can also access billing data and is billed for this account. |



## Get Ad Account User

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/v72c09s/user-access)

Fetching an ad account user requires both the `account` and `user` keys to look up an existing ad account user.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-request-2)

### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccountUsers/(account=urn:li:sponsoredAccount:516986977,user=urn:li:person:_mVMF2Kp8p)

```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-response)

### Sample Response

JSON

```
{
    "account": "urn:li:sponsoredAccount:516986977", 
    "changeAuditStamps": {
        "created": {
            "actor": "urn:li:unknown:0", 
            "time": 1509484800000
        }, 
        "lastModified": {
            "actor": "urn:li:unknown:0", 
            "time": 1509484800000
        }
    }, 
    "role": "CAMPAIGN_MANAGER", 
    "user": "urn:li:person:_mVMF2Kp8p", 
    "version": {
        "versionTag": "1"
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#find-ad-accounts-by-authenticated-user)

## Find Ad Accounts by Authenticated User

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/v72c09s/user-access)

All ad accounts that an authenticated user has access to can be retrieved with the following Find Ad Account endpoint. The only required parameter is `q=authenticatedUser`. This returns all ad accounts associated with the member whose access token is being used in the call.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-request-3)

### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_4_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_4_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccountUsers?q=authenticatedUser
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-response-1)

### Sample Response

JSON

```
{
    "elements": [
        {
            "account": "urn:li:sponsoredAccount:516413367",
            "changeAuditStamps": {
                "created": {
                    "actor": "urn:li:unknown:0",
                    "time": 1500331577000
                },
                "lastModified": {
                    "actor": "urn:li:unknown:0",
                    "time": 1505328748000
                }
            },
            "role": "ACCOUNT_BILLING_ADMIN",
            "user": "urn:li:person:K1RwyVNukt",
            "version": {
                "versionTag": "89"
            }
        },
        {
            "account": "urn:li:sponsoredAccount:516880883",
            "changeAuditStamps": {
                "created": {
                    "actor": "urn:li:unknown:0",
                    "time": 1505326590000
                },
                "lastModified": {
                    "actor": "urn:li:unknown:0",
                    "time": 1505326615000
                }
            },
            "role": "ACCOUNT_BILLING_ADMIN",
            "user": "urn:li:person:K1RwyVNukt",
            "version": {
                "versionTag": "3"
            }
        }
    ],
    "paging": {
        "count": 2,
        "links": [],
        "start": 0,
        "total": 2
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#find-ad-account-users-by-accounts)

## Find Ad Account Users by Accounts

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/v72c09s/user-access)

The inverse of the previous endpoint is to fetch all users associated with a specific ad account. This endpoint requires the `q=accounts` parameter and supports searching users by only a single ad account. It only returns matching results of the first account ID in the `accounts` query parameter even if there are multiple account IDs in the `accounts` query parameter.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_5_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_5_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccountUsers?q=accounts&accounts={sponsoredAccountUrn}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-request-4)

### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_6_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#tabpanel_6_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccountUsers?q=accounts&accounts=urn:li:sponsoredAccount:516986977
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02&tabs=http#sample-response-2)

### Sample Response

JSON

```
{
    "elements": [
        {
            "account": "urn:li:sponsoredAccount:516986977",
            "changeAuditStamps": {
                "created": {
                    "time": 1509484815000
                },
                "lastModified": {
                    "time": 1509484815000
                }
            },
            "role": "CAMPAIGN_MANAGER",
            "user": "urn:li:person:AeioYvX34u"
        },
        {
            "account": "urn:li:sponsoredAccount:516986977",
            "changeAuditStamps": {
                "created": {
                    "time": 1505858342000
                },
                "lastModified": {
                    "time": 1509750585000
                }
            },
            "role": "ACCOUNT_BILLING_ADMIN",
            "user": "urn:li:person:K1RwyVNukt"
        }
    ],
    "paging": {
        "count": 2,
        "links": [],
        "start": 0,
        "total": 2
    }
}
```


| Scenario                 | Message                                                                                                                                                      | Reason                                | Type          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- | ------------- |
| Updating Ad Account User | The account ID `account` in the query parameters doesn't match the account ID `account` in the body.                                                         | ACCOUNT_ID_MISMATCH_IN_PARAM_AND_BODY | INVALID_VALUE |
| Creating Ad Account User | A confirmed primary email is required but is not present for account `account`. Please set a primary email and make sure it's confirmed.                     | MEMBER_HAD_UNCONFIRMED_EMAIL          | INVALID_VALUE |
| Updating Ad Account User | This request has multiple accounts associated with it, but batch request only supports operations on a single account. Separate the requests by account URN. | MULTIPLE_ACCOUNTS_UNSUPPORTED         | INVALID_VALUE |
| Updating Ad Account User | The user ID `user` in the query parameters doesn't match the user ID `user` in the body.                                                                     | USER_MISMATCH_IN_PARAM_AND_BODY       | INVALID_VALUE |


# Account Access Controls# Account Access Controls
## Permissions

You need the following scope permissions along with **one** of the listed Ad Account roles:

Scope permissions:

- `rw_ads` (Read/Write).
- `r_ads` (Read-Only).

Ad Account Roles:

- `ACCOUNT_BILLING_ADMIN`
- `ACCOUNT_MANAGER`
- `CAMPAIGN_MANAGER`
- `CREATIVE_MANAGER`
- `VIEWER` (Read-Only, even with rw_ads scope).

## Ad Account User Role Definitions

The following table describes in detail what each role provides:

| Control Name          | Description                                                                                                                                                                                                                                                                               |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| VIEWER                | View campaign data and reports for the account. No ability to create or edit campaigns or ads                                                                                                                                                                                             |
| CREATIVE_MANAGER      | View campaign data and reports for the account. Ability to create and edit ads                                                                                                                                                                                                            |
| CAMPAIGN_MANAGER      | View campaign data and reports for the account. Ability to create and edit campaigns and ads                                                                                                                                                                                              |
| ACCOUNT_MANAGER       | View campaign data and reports for the account. Ability to create and edit campaigns and ads. Edit account data and manage user access for the account.                                                                                                                                   |
| ACCOUNT_BILLING_ADMIN | View campaign data and reports for the account. Ability to create and edit campaigns and ads. Edit account data and manage user access for the account. Can also access billing data and is billed for this account. Note: There should be exactly one user with this role in an account. |


## Grant User Access
Each user account can be described by the `AccountUser` object. For more details please refer to [Create and Manage Account Users](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-account-users?view=li-lms-2026-02).

This object consists of the following field types:

| Field   | Type            | Description                                                                                                                                                           |
| ------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| account | URN             | The Ad Account URN to which access is being granted.                                                                                                                  |
| user    | URN             | The user URN that you intend to grant access to.                                                                                                                      |
| role    | AccountUserRole | The access type that's granted to the user. Valid values include:- VIEWER<br>- CREATIVE_MANAGER<br>- CAMPAIGN_MANAGER<br>- ACCOUNT_MANAGER<br>- ACCOUNT_BILLING_ADMIN |



### Sample Request

In the example below, a member is granted read-only access to the Ad account. The body of the `PUT` request is an `adAccountUser` object with `VIEWER` for the role field.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#tabpanel_1_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#tabpanel_1_curl)

HTTP

```
PUT https://api.linkedin.com/rest/adAccountUsers/(account=urn:li:sponsoredAccount:123456789,user=urn:li:person:qZXYVUTSR)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#sample-response)

### Sample Response

JSON

```
{
    "account": "urn:li:sponsoredAccount:12345...",
    "role": "VIEWER",
    "user": "urn:li:person:56789..."
}
```

## Fetch Existing Ad Account Users

When making a `GET` call to fetch existing users on an account, the authenticated user can only view themselves unless they're an account manager.
### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccountUsers?accounts=urn:li:sponsoredAccount:123456789&q=accounts
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/account-access-controls?view=li-lms-2026-02&tabs=http#sample-response-1)

### Sample Response

JSON

```
{
    "paging": {
        "start": 0,
        "count": 2147483647,
        "links": [],
        "total": 1
    },
    "elements": [
        {
            "role": "ACCOUNT_BILLING_ADMIN",
            "changeAuditStamps": {
                "created": {
                    "time": 1619111821000
                },
                "lastModified": {
                    "time": 1619111821000
                }
            },
            "user": "urn:li:person:userId",
            "account": "urn:li:sponsoredAccount:123456789"
        }
    ]
}
```


# Create and Manage Campaign Groups
Campaign groups provide advertisers a way to manage status, budget, and performance across multiple related campaigns.

Whenever an Ad Account is created, a new campaign group is automatically created for it.

A campaign group can contain a variety of campaign types. There is no limit to the number of campaign groups per advertiser account. Note that LinkedIn imposes a limit of 5,000 campaigns per advertiser account and 2,000 campaigns per non-default campaign group.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#permissions)

## Permissions

two conditions for successful Ad Account Users API calls:

- Scope permission accessibility for:
    
    - `rw_ads` (read/write).
    - `r_ads` (read-only)
- The Ad Account user assigning permission holding one of the following Ad Account roles:
    
    - `ACCOUNT_BILLING_ADMIN`
    - `ACCOUNT_MANAGER`
    - `CAMPAIGN_MANAGER`
    - `CREATIVE_MANAGER`
    - `VIEWER` (read-only, even with `rw_ads` scope)

### Pagination for non-search APIs

The `adCampaignGroups` API implements pagination using the `start` and `count` parameters for several methods. The max `count` value is 1000. A `400 Bad Request` response with the message, "Specified count is larger than 1000" is returned if:

- The `count` is greater than 1000.
- The number of elements in the response is greater than 100, and the API request doesn't contain pagination request parameters.

For more information, see [Pagination](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/pagination?view=li-lms-2026-02).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#schema)

## Schema

 Note

Starting 202211, response decoration is no longer supported and has been replaced by Additional Info Fields. These new field(s) provide additional information for a field that's present in a schema. Learn more about the Additional Info Fields [here](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02). The fields `budgetOptimization.bidStrategy` and `budgetOptimization.budgetOptimizationStrategy`are only supported starting from API versions 202501.

|Field Name|Type|Description|Additional Info Field|
|---|---|---|---|
|account|SponsoredAccountUrn|URN identifying the advertising account associated with the campaign. This value is immutable once set. For example, `urn:li:SponsoredAccount:{id}`.|False|
|accountInfo|[Account](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-accounts?view=li-lms-2026-02#schema)|Information about the advertising account associated with the campaign. This is a read only field. Please refer to [Additional Info Fields](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02) to learn how to access this field.|True|
|backfilled|boolean, default="false"|Flag that denotes whether the campaign group was created organically or to backfill existing campaigns. This is a read-only field set by the system.|False|
|id|long|Numerical identifier for the campaign group. This is a read-only field set by the system.|False|
|name|string|The name of the campaign group used to make it easier to reference a campaign group and recall its purpose. The value of this field can't exceed 100 characters.|False|
|runSchedule.start|long|Represents the inclusive (greater than or equal to) date when to start running the associated campaigns under this campaign group. This field is required.|False|
|runSchedule.end|optional long|Represents the exclusive (strictly less than) date when to stop running the associated campaigns under this campaign group. If this field is unset, it indicates an open range with no end date. This field is required if `totalBudget` is set.|False|
|`servingStatuses`|string[]|Array of enums that determine whether or not campaigns within the campaign group may be served. Unlike `status`, which is user-managed, the values are controlled by the service. This is a read-only field. Possible values are:- RUNNABLE Campaign group is currently active; billing information, budgetary constraints, or start and end dates are valid.<br>- STOPPED Campaign group is currently not eligible for serving for reasons other than billing information, budgetary constraints, or termination dates. For instance, a campaign group will be STOPPED if it has been canceled by the user, or it's marked as spam.<br>- BILLING_HOLD Parent account is on billing hold.<br>- ACCOUNT_TOTAL_BUDGET_HOLD Parent account total budget has been reached.<br>- ACCOUNT_END_DATE_HOLD Parent account end date has been reached.<br>- CAMPAIGN_GROUP_TOTAL_BUDGET_HOLD Campaign group total budget has been reached.<br>- CAMPAIGN_GROUP_START_DATE_HOLD Campaign group start date is in the future.<br>- CAMPAIGN_GROUP_END_DATE_HOLD Campaign group end date has been reached.|False|
|status|string|Status of campaign group. Possible values are:- ACTIVE - Denotes that the campaign group is capable of serving ads, subject to run date and budget limitations (as well as any other limitations at the account or campaign level).<br>- ARCHIVED - Denotes that the campaign group is presently inactive, and should mostly be hidden in the UI until un-archived.<br>- CANCELLED - Denotes that the campaign group has been permanently canceled and can't be reactivated. Not a settable status.<br>- DRAFT - Denotes that the campaign group is in a preliminary state and should temporarily not be served.<br>- PAUSED - Denotes that the campaign group meets all requirements to be served, but temporarily shouldn't be.<br>- PENDING_DELETION - Denotes that the campaign group has been requested to be deleted that's currently pending.<br>- REMOVED - Denoted that the campaign group was deleted, but must remain fetchable due to the existence of performance data.|False|
|`totalBudget.amount`|BigDecimal|If `budgetOptimization.budgetOptimizationStrategy` is `DYNAMIC`, the total budget of the campaign group will be shared among all campaigns within the same campaign group. Otherwise, it represents the maximum amount to be spent across all associated campaigns and creatives for the duration of the campaign group.|False|
|`totalBudget.currencyCode`|Currency|Indicates the `currencyCode` of the campaign group's total budget. `Note`: The currency must match the ISO currency code of the account.|False|
|`test`|boolean, default="false"|Flag showing whether this campaign group is a test campaign group, i.e., belongs to a test account. This is a read-only and immutable field that's set implicitly during creation based on whether the account is a Test Account or not.|False|
|`allowedCampaignTypes`|string[]|Array of enums that indicates allowed campaign types within the specific campaign group. Possible values are:- TEXT_AD - Text-based ads that show up in the right column or top of the page on LinkedIn.<br>- SPONSORED_UPDATES - Native ads that promote a company's content updates in the LinkedIn feed.<br>- SPONSORED_INMAILS - Personalized messages with a call-to-action button delivered to a LinkedIn's member inbox.<br>- DYNAMIC - Ads that are dynamically personalized. This is a read-only field.|False|
|`objectiveType`|string|Campaign Group Objective type values. This field is optional and immutable. Campaigns in this group will automatically have the same objective type. [Click here for Objective descriptions](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ad-budget-pricing-type-combinations?view=li-lms-2026-02)- BRAND_AWARENESS<br>- ENGAGEMENT<br>- JOB_APPLICANTS<br>- LEAD_GENERATION<br>- WEBSITE_CONVERSIONS<br>- WEBSITE_VISIT<br>- VIDEO_VIEWS||
|`budgetOptimization.bidStrategy`|string|Denotes the strategy used for bidding in auction. Campaigns under the campaign group must have the same bid strategy. Possible values:- MAXIMUM_DELIVERY<br>- MANUAL<br>- COST_CAP||
|`budgetOptimization.budgetOptimizationStrategy`|string|Strategy used for campaign group budgeting to decide how to allocate budget across campaigns under the campaign group. Possible values:- DYNAMIC||
|`dailyBudget`|BigDecimal|Daily budget for the campaign group and will be shared among all campaigns within the campaign group. This field is optional and mutable. It can only be used if `budgetOptimization.budgetOptimizationStrategy` is `DYNAMIC` `Note`: This field applies to API Versions starting from 202504 and later.|False|


## Get a Campaign Group

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/wk49iky/campaign-group-management)

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_2_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_2_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/adCampaignGroups/{adCampaignGroupsId}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#sample-response)

#### Sample Response

JSON

```
{
    "account": "urn:li:sponsoredAccount:512358882",
    "backfilled": false,
    "changeAuditStamps": {
        "created": {
            "actor": "urn:li:person:324_kGGaLE",
            "time": 1490074934000
        },
        "lastModified": {
            "actor": "urn:li:unknown:0",
            "time": 1490074934000
        }
    },
    "id": 512358882,
    "name": "New Campaign Group",
    "runSchedule": {
        "end": 9876543210123,
        "start": 1234567890987
    },
    "test": false,
    "servingStatuses": [
        "BILLING_HOLD"
    ],
    "allowedCampaignTypes": [
        "SPONSORED_UPDATES",
        "TEXT_AD"
    ],
    "status": "ACTIVE"
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#search-for-campaign-groups)

## Search for Campaign Groups

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/wk49iky/campaign-group-management)

 Note

From 202401 version and above, we have moved from index based pagination to cursor based pagination for our search APIs.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#cursor-based-pagination-for-search-apis)

### Cursor based Pagination for search APIs

The adCampaignGroups API implements cursor based pagination using the pageSize and pageToken parameters for search method. The max allowed pageSize is 1,000.

- pageSize governs the number of requested entities
- pageToken is used to get the next set of results.
    - nextPageToken is returned in metadata field of the search response.
    - This should be passed in pageToken query parameter in the request to get the next page of results.

Use the `q=search` parameter with to search for campaign groups by ID, name, and status fields. Search criteria is mandatory and can be chained together for increased granularity.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/adCampaignGroups?q=search&search=(searchCriteria:(values:List(searchValue)))
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#parameters)

#### Parameters

|Field Name|Required|Description|
|---|---|---|
|search.id.values|no|Searches for campaign groups by ID. For example, `urn:li:sponsoredCampaignGroup:{campaignGroupId}`|
|search.status.values|no|Searches for campaign groups with the provided status. The possible values are:- ACTIVE<br>- ARCHIVED<br>- CANCELED<br>- DRAFT<br>- PAUSED<br>- PENDING_DELETION<br>- REMOVED|
|search.name.values|no|Searches for campaign groups by name.|
|search.test|no|Searches for campaign groups based on test or non-test.- true: for test campaign groups<br>- false: for non-test campaign groupsIf not specified, searches for both test and non-test campaign groups.|
|sortOrder|no|Specifies the sort order of the results. Results will be sorted by campaign group id. Supported values include:- ASCENDING<br>- DESCENDING The default is "ASCENDING".|
|pageSize|no|Specifies the number of entities to be returned. The default is 100. Max is 1,000.|
|pageToken|no|Unique key representing the last entity of the response. This is to be used to fetch the next set of entities. If less than pageSize entities are returned in the current response, pageToken will be null|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#sample-request)

#### Sample Request

The following example searches for all campaign groups in `ACTIVE` and `DRAFT` status. The results are ordered by `id` in descending order.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_4_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_4_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/506223315/adCampaignGroups?q=search&search=(status:(values:List(ACTIVE,DRAFT)))&sortOrder=DESCENDING
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#sample-response-1)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "runSchedule": {
                "end": 9876543210123,
                "start": 1234567890987
            },
            "changeAuditStamps": {
                "created": {
                    "time": 1542042798000
                },
                "lastModified": {
                    "time": 1542129293297
                }
            },
            "name": "Refresh group",
            "test": false,
            "servingStatuses": [
                "CAMPAIGN_GROUP_END_DATE_HOLD",
                "BILLING_HOLD"
            ],
            "allowedCampaignTypes": [
                "SPONSORED_UPDATES",
                "TEXT_AD"
            ],
            "backfilled": false,
            "id": 603407684,
            "account": "urn:li:sponsoredAccount:506223315",
            "status": "ACTIVE"
        },
        {
            "runSchedule": {
                "start": 1493228897000
            },
            "changeAuditStamps": {
                "created": {
                    "time": 1493228897000
                },
                "lastModified": {
                    "time": 1493228897000
                }
            },
            "name": "New Campaign Group",
            "test": false,
            "servingStatuses": [
                "BILLING_HOLD"
            ],
            "allowedCampaignTypes": [
                "SPONSORED_UPDATES",
                "TEXT_AD"
            ],
            "backfilled": false,
            "id": 504293601,
            "account": "urn:li:sponsoredAccount:506223315",
            "status": "ACTIVE"
        }
    ],
    "metadata": {
        "nextPageToken": "DgGerr1iVQreCJVjDOW_rcp63nueBDipsS4DJpvJo"
    }
}
```

 Note
API Call to get the next set of results would use the nextPageToken passed in the response above.
GET https://api.linkedin.com/rest/adAccounts/506223315/adCampaignGroups?q=search&search=(status:(values:List(ACTIVE,DRAFT)))&sortOrder=DESCENDING&pageToken=DgGerr1iVQreCJVjDOW_rcp63nueBDipsS4DJpvJo


### Batch Get Campaign Groups

Multiple campaign groups can be requested in a single call by chaining together `ids` parameters that each have a corresponding campaign group ID.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_10_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_10_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/adCampaignGroups?ids=List(campaignGroupId1,campaignGroupId2)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#sample-request-4)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_11_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#tabpanel_11_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/512352200/adCampaignGroups?ids=List(604716224,604716214)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02&tabs=http#sample-response-2)

#### Sample Response

JSON

```
{
    "errors": {},
    "results": {
        "604716214": {
            "account": "urn:li:sponsoredAccount:512352200",
            "backfilled": false,
            "changeAuditStamps": {
                "created": {
                    "actor": "urn:li:person:324_kGGaLE",
                    "time": 1494970241000
                },
                "lastModified": {
                    "actor": "urn:li:unknown:0",
                    "time": 1494970241000
                }
            },
            "id": 604716214,
            "name": "CampaignGroup2",
            "runSchedule": {
                "end": 9876543210123,
                "start": 1234567890987
            },
            "test": false,
            "servingStatuses": [
                "BILLING_HOLD"
            ],
            "allowedCampaignTypes": [
                "SPONSORED_UPDATES",
                "TEXT_AD"
            ],
            "status": "ACTIVE",
            "totalBudget": {
                "amount": "60000",
                "currencyCode": "USD"
            }
        },
        "604716224": {
            "account": "urn:li:sponsoredAccount:512352200",
            "backfilled": false,
            "changeAuditStamps": {
                "created": {
                    "actor": "urn:li:person:324_kGGaLE",
                    "time": 1494970241000
                },
                "lastModified": {
                    "actor": "urn:li:unknown:0",
                    "time": 1494970241000
                }
            },
            "id": 604716224,
            "name": "CampaignGroup3",
            "test": false,
            "runSchedule": {
                "end": 9876543210123,
                "start": 1234567890987
            },
            "servingStatuses": [
                "BILLING_HOLD"
            ],
            "allowedCampaignTypes": [
                "SPONSORED_UPDATES",
                "TEXT_AD"
            ],
            "status": "ACTIVE",
            "totalBudget": {
                "amount": "30000",
                "currencyCode": "USD"
            }
        }
    },
    "statuses": {}
}
```

## Campaign Schema

 Note

Starting 202211, response decoration is no longer supported and has been replaced by Additional Info Fields. These new field(s) provide additional information for a field that's present in a schema. Learn more about the Additional Info Fields [here](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02).

|Field|Type|Description|Required|Additional Info Field|
|---|---|---|---|---|
|account|SponsoredAccountUrn|URN identifying the advertising account associated with the campaign. This value is immutable once set. For example, urn:li:sponsoredAccount:{id}|True|False|
|accountInfo|[Account](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-accounts?view=li-lms-2026-02#schema)|Information about the advertising account associated with the campaign. This is a read only field. Please refer to [Additional Info Fields](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02) to learn how to access this field.|False|True|
|associatedEntity|URN|An URN identifying the intended beneficiary of the advertising campaign such as a specific company or member|False unless campaign will use Sponsored Content, Dynamic Ads, or Lead Gen Forms|False|
|associatedEntityInfo|Union|Information about the associatedEntity. If the entity is an organization, an [OrganizationInfo](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#organizationinfo) object is returned. If the entity is a person, a [PersonInfo](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#personinfo) object is returned. For all other entity types an empty record will be returned. This is a read only field. Please refer to [Additional Info Fields](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02) to learn how to access this field.|False|True|
|audienceExpansionEnabled|boolean, default="false"|Enable Audience Expansion for the campaign provides query expansion for certain targeting criteria.|False|False|
|campaignGroup|Sponsored-CampaignGroup URN|URN identifying the campaign group associated with the campaign. The campaign group URN must be specified for campaign creation starting October 30, 2020.|True|False|
|campaignGroupInfo|[CampaignGroup](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaign-groups?view=li-lms-2026-02#schema)|Information about the Campaign Group associated with the campaign. This is a read only filed. Please refer to [Additional Info Fields](https://learn.microsoft.com/en-us/linkedin/marketing/additional-info-field?view=li-lms-2026-02) to learn how to access this field.|False|True|
|costType|CostType|- CPM- Cost per thousand advertising impressions. If type=SPONSORED_INMAILS; cost per send(CPS) is measured as CPM x 1000.<br>- CPC- Cost per individual click on the associated link.<br>- CPV- Cost per view for video ads.|True|False|
|creativeSelection|CampaignCreativeSelection, default="OPTIMIZED"|- ROUND_ROBIN - Rotate through available creatives to serve them as evenly as possible.<br>- OPTIMIZED - Bias selection taking into account such as expected performance. Not available for Message and Conversation Ads (type=SPONSORED_INMAILS).|False|False|
|dailyBudget.amount|BigDecimal|Maximum amount to spend per day UTC. The amount of money as a real number string.|True, unless totalBudget is provided.|False|
|dailyBudget.currencyCode|Currency|ISO currency code. The currency must match that of the parent account.|True, unless totalBudget is provided.|False|
|locale.country|string|Locale of the campaign. An uppercase two-letter country code as defined by ISO-3166. The country and language combination must match one of the [supported locales](https://learn.microsoft.com/en-us/linkedin/shared/references/reference-tables/language-codes?view=li-lms-2026-02)|True|False|
|locale.language|string|Locale of the campaign. A lowercase two-letter language code as defined by ISO-639. The country and language combination must match one of the [supported locales](https://learn.microsoft.com/en-us/linkedin/shared/references/reference-tables/language-codes?view=li-lms-2026-02)|True|False|
|name|string|The name of the campaign; primarily used to make it easier to reference a campaign and to recall its purpose.|True|False|
|objectiveType|string|Campaign Objective type values. [Click here for Campaign Objective descriptions](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ad-budget-pricing-type-combinations?view=li-lms-2026-02)- BRAND_AWARENESS<br>- ENGAGEMENT<br>- JOB_APPLICANTS<br>- LEAD_GENERATION<br>- WEBSITE_CONVERSIONS<br>- WEBSITE_VISITS<br>- VIDEO_VIEWS|False|False|
|offsiteDeliveryEnabled|Boolean (True/False)|Allows your campaign to be served on the LinkedIn Audience Network to extend the reach of the campaign by delivering ads beyond the LinkedIn feed to members on third-party apps and sites. There is no default set.|True|False|
|offsitePreferences|[OffsitePreferences](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#offsite-preferences)|Offsite preferences that an advertiser specifies for this campaign. An example OffsitePreference is an object that contains App Categories, App Store URLs, Web Domain Names for which this campaign should be included/excluded. See the OffsitePreferences object for more details and examples.|False|False|
|runSchedule.start|long|Scheduled date range to run associated creatives. The start date must be non-null. Represents the inclusive (greater than or equal to) value in which to start the range.|False|False|
|runSchedule.end|long|Scheduled date range to run associated creatives. The start date must be non-null. Represents the exclusive (strictly less than) value in which to end the range. This field is optional. An unset field indicates an open range; for example, if start is 1455309628000 (Fri, 12 Feb 2016 20:40:28 GMT), and end is not set, it means everything at, or after 1455309628000.|False|False|
|targetingCriteria|[targetingCriteria](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/targeting-criteria?view=li-lms-2026-02)|Specifies targeting criteria that the member should match. This is a more advanced boolean expression than the previous targeting field. It provides a generic AND/OR construct to include and exclude different targeting facets when defining audiences for campaigns.|True, unless targeting provided.|False|
|totalBudget.amount|BigDecimal|Maximum amount to spend over the life of the campaign. The amount of money as a real number string. Deprecated for campaigns not using lifetime pacing.|True, unless dailyBudget is provided.|False|
|totalBudget.currencyCode|Currency|ISO currency code. The currency must match that of the account. Deprecated for campaigns not using lifetime pacing.|True, unless dailyBudget is provided.|False|
|type|CampaignType|- TEXT_AD - Text-based ads that show up in the right column or top of the page on LinkedIn.<br>- SPONSORED_UPDATES - Native ads that promote a company's content updates in the LinkedIn feed.<br>- SPONSORED_INMAILS - Personalized messages with a call-to-action button delivered to a LinkedIn's member inbox.<br>- DYNAMIC - Ads that are dynamically personalized.|True|False|
|unitCost.amount|BigDecimal, default=0|This value is used as one of the following: amount to bid (for manual bidding), amount which is the target cost (for target cost bidding) per click, impression, or other event depending on the pricing model, or cost cap (for cost cap bidding). The amount of money as a real number string. The amount should be non-negative if the bidding strategy is manual, target cost, or cost cap bidding. The default is 0 with the currency code set to match that of the associated account.|True|False|
|unitCost.currencyCode|Currency  <br>default is set to match the associated account|Amount to bid per click, impression, or other event depending on the pricing model. The default is 0 with the currency code set to match that of the associated account. ISO currency code.|False|False|
|versionTag|string|Each entity has a version tag associated with it. The version tag is initiated to 1 when the entity is created. Each single update to the entity increases its version tag by 1.|False|False|
|status|string|- ACTIVE - Denotes that the campaign is fully servable.<br>- PAUSED - Denotes that the campaign meets all requirements to be served, but temporarily shouldn't be.<br>- ARCHIVED - Denotes that the campaign is presently inactive, and should mostly be hidden in the UI until un-archived.<br>- COMPLETED - Denotes that the campaign has reached a specified budgetary or chronological limit.<br>- CANCELED - Denotes that the campaign has been permanently canceled, such as when an advertising account is permanently closed.<br>- DRAFT - Denotes that the campaign is still being edited and not eligible for serving. Some validation will be postponed until the campaign is activated.<br>- PENDING_DELETION - Denotes that the campaign has been requested to be deleted that's currently pending.<br>- REMOVED - Denotes that the campaign was deleted, but must remain fetchable due to the existence of performance data.|True|False|
|optimizationTargetType|default="NONE"|Determines how this campaign is optimized for spending. If this is not set, there's no optimization. Refer to the documentation [here](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#optimization-of-campaigns).|False|False|
|format|campaignFormat|The ad format on campaign level.  <br>Read more: [Ad Formats](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/campaign-formats?view=li-lms-2026-02)|False|False|
|pacingStrategy|string|Identifies the pacing option used for the campaign.  <br>Optional and editable only on create. Possible values:- LIFETIME - [Lifetime pacing](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02#lifetime-pacing) that optimizes campaign budget delivery throughout campaign's lifetime.<br>- ACCELERATED - [Accelerated pacing](https://www.linkedin.com/help/lms/answer/a6598492) is a pacing option that can maximize reach and delivery during an event as it works to deliver your campaign budget to your target audience as quickly as possible.<br>- The field is only available from version 202501 and above.|False|False|
|test|boolean, default="False"|Flag showing whether this campaign is a test campaign, i.e., belongs to a test account. This is a read-only and immutable field that's set implicitly during creation based on whether the account is a Test Account or not.|False|False|
|servingStatuses|strings|Array of enums that determine whether or not a campaign may be served; unlike 'status', which is user-managed, the values are controlled by the service. This is a read-only field. Possible values are:- RUNNABLE Campaign is eligible for serving.<br>- STOPPED Campaign is currently not servable for reasons other than billing information, budgetary constraints, or termination dates. For instance, an campaign will be STOPPED if it has been PAUSED by the user.<br>- ACCOUNT_TOTAL_BUDGET_HOLD Parent account total budget has been reached.<br>- ACCOUNT_END_DATE_HOLD Parent account end date has been reached.<br>- CAMPAIGN_START_DATE_HOLD Campaign start date is in the future.<br>- CAMPAIGN_END_DATE_HOLD Campaign end date has been reached.<br>- CAMPAIGN_TOTAL_BUDGET_HOLD Campaign total budget has been reached.<br>- CAMPAIGN_AUDIENCE_COUNT_HOLD Campaign is on hold because it has an audience count lower than the threshold.<br>- CAMPAIGN_GROUP_START_DATE_HOLD Campaign group start date is in the future.<br>- CAMPAIGN_GROUP_END_DATE_HOLD Campaign Group end date is in the past.<br>- CAMPAIGN_GROUP_TOTAL_BUDGET_HOLD Campaign group total budget has been reached.<br>- CAMPAIGN_GROUP_STATUS_HOLD Campaign group status is on hold.<br>- ACCOUNT_SERVING_HOLD Parent account is on hold and not eligible for serving.|False|False|
|connectedTelevisionOnly|Boolean Optional, default="False"|Flag showing whether this campaign is a Connected Television Only campaign. Allow advertisers to specify when they’re creating a CTV campaign. Not specifying the boolean can be considered false. When 'connectedTelevisionOnly = true', offsiteDeliveryEnabled should be set to true. Note: Applicable only from versions 202408 and above.|False|False|
|optimizationPreference|Union|Allows granular optimization customization on this campaign on top of optimizationTargetType. [FrequencyOptimizationPreference](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#frequency-optimization-preference) is the first type of optimizationPreference we support now. Note: Applicable only from versions 202408 and above.|False|False|
|politicalIntent|string|Enum indicating whether a campaign is categorized as a political campaign. This allows advertisers to declare whether their ad constitutes political advertising. This field can be updated when the targeting of campaign changes. The possible values are:- `POLITICAL`: Campaign is political advertising.<br>- `NOT_POLITICAL`: Campaign is not a political advertising.<br>- `NOT_DECLARED`: Indicates that the campaign's political intent hasn't been specified.|True|False|

 Important

Applications that integrate with LinkedIn's Advertising APIs to create ads must display the following consent to advertisers when targeting EU region and pass back the consent obtained by setting the field `politicalIntent`: _I confirm this is not political advertising. None of my ads qualify as political advertising under the law of the targeted countries, including EU law for ads targeted to the EU. Advertisers must comply with Linkedin's policies and regulatory requirements. [Learn more](https://www.linkedin.com/legal/ads-policy)_ This notice must be clearly presented and checked by default during the campaign creation process in the partner interface before submitting or activating campaigns targeting the EU region.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#organizationinfo)

### OrganizationInfo

|Field Name|Type|Description|
|---|---|---|
|id|long|Unique Id representing the organization.|
|name|[MultiLocaleString](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02#multilocalestring)|Name of the organization.|
|vanityName|string|Name of the organization present in the URLs.|
|localizedName|string|Locale specific name of the organization.|
|logo|[CroppedImage](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02#croppedimage)|The organization’s logo. The sizes may vary greatly, i.e., 50x50, 100x60, 400x400, so clients should handle the given height and width accordingly.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#personinfo)

### PersonInfo

|Field Name|Type|Description|
|---|---|---|
|id|URN|Unique id representing the member|
|vanityName|String|Name of the member present in the URLs.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#targeting-object)

### Targeting Object

The `targeting` object is deprecated. Campaigns should use the [`targetingCriteria`](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/targeting-criteria?view=li-lms-2026-02) object going forward. See the [Migration Guide for targetingCriteria](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/migration-targeting-criteria?view=li-lms-2026-02) for more information.

Once a campaign is using the preferred `targetingCriteria` format, it can't be changed back to the `targeting` format. All further targeting updates must use the `targetingCriteria` format.
## Get a Campaign

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/pvhqngd/campaign-mangement)

Campaigns can be retrieved individually by passing in their ID to the following endpoint:

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#tabpanel_5_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#tabpanel_5_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/adCampaigns/{campaignID}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#sample-response)

#### Sample Response

JSON

```
{
    "account": "urn:li:sponsoredAccount:506289162",
    "associatedEntity": "urn:li:organization:2414183",
    "audienceExpansionEnabled": false,
    "campaignGroup": "urn:li:sponsoredCampaignGroup:602277684",
    "changeAuditStamps": {
        "created": {
            "time": 1530119777000
        },
        "lastModified": {
            "time": 1530119777000
        }
    },
    "costType": "CPC",
    "connectedTelevisionOnly": false,
    "creativeSelection": "OPTIMIZED",
    "dailyBudget": {
        "amount": "1800",
        "currencyCode": "USD"
    },
    "id": 141049524,
    "locale": {
        "country": "US",
        "language": "en"
    },
    "name": "Campaign Sponsored update B",
    "offsiteDeliveryEnabled": false,
    "optimizationPreference": {
        "frequencyOptimizationPreference": {
            "timeSpan": {
                "duration": 7,
                "unit": "DAY"
            },
            "optimizationType": "MAX_FREQUENCY",
            "frequency": 10
        }
    },
    "optimizationTargetType": "NONE",
    "test": false,
    "runSchedule": {
        "end": 9876543210123,
        "start": 1234567890987
    },
    "servingStatuses": [
        "ACCOUNT_SERVING_HOLD"
    ],
    "status": "ACTIVE",
    "targeting": {
        "includedTargetingFacets": {
            "employers": [
                "urn:li:organization:0000"
            ],
            "interfaceLocales": [
                {
                    "country": "US",
                    "language": "en"
                }
            ],
            "locations": [
                "urn:li:geo:103644278"
            ]
        }
    },
    "targetingCriteria": {
        "include": {
            "and": [
                {
                    "or": {
                        "urn:li:adTargetingFacet:employers": [
                            "urn:li:company:0000"
                        ]
                    }
                },
                {
                    "or": {
                        "urn:li:adTargetingFacet:locations": [
                            "urn:li:geo:103644278"
                        ]
                    }
                },
                {
                    "or": {
                        "urn:li:adTargetingFacet:interfaceLocales": [
                            "urn:li:locale:en_US"
                        ]
                    }
                }
            ]
        }
    },
    "type": "SPONSORED_UPDATES",
    "unitCost": {
        "amount": "15",
        "currencyCode": "USD"
    },
    "version": {
        "versionTag": "1"
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#search-for-campaigns)

## Search for Campaigns

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/pvhqngd/campaign-mangement)

 Note

From 202401 version and above, we have moved from index based pagination to cursor based pagination for our search APIs.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#cursor-based-pagination-for-search-apis)

### Cursor based Pagination for search APIs

The adCampaigns API implements cursor based pagination using the pageSize and pageToken parameters for search method. The max allowed pageSize is 1,000.

- pageSize governs the number of requested entities
- pageToken is used to get the next set of results.
- nextPageToken is returned in metadata field of the search response.
- This should be passed in pageToken query parameter in the request to get the next page of results.

Search for campaigns by ID, campaign group, name, type, and status fields. Search criteria is mandatory and can be chained together for increased granularity.

If you're using the Search for Campaigns endpoint and the response returns more than 1,000 campaigns, the API returns a `400` error with the following message:

`{"message":"Request would return too many entities. ","status":400}`

If more than 1,000 campaigns need to be pulled, set a pageSize parameter value of less than 1,000 to pull less than 1,000 campaigns per call and paginate through the full list of campaigns using pageToken.

 Note

This call may return both _test_ and _non-test_ campaigns.

To search for _non-test campaigns_ only, filter out the test campaigns by specifying `search.test=False`  
If you would like to search only _test campaigns_, specify `search.test=True`.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#tabpanel_6_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#tabpanel_6_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/adCampaigns?q=search&search=(searchCriteria:(values:List(searchValue)))
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-campaigns?view=li-lms-2026-02&tabs=http#parameters)

# # Creatives
|ield Name|Required|Type|Description|
|---|---|---|---|
|account|No|Sponsored Account URN|URN identifying the advertising account associated with the creative. This field is read-only.|
|campaign|Yes|Sponsored Campaign URN|URN identifying the campaign associated with the creative|
|content|No|Underlying content URN|Content sponsored in the creative. On creation, it can be dynamic Ad content ([follower](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/follower-ads?view=li-lms-2026-02), [job](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/jobs-ads-integrations?view=li-lms-2026-02), [spotlight](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/spotlight-ads?view=li-lms-2026-02)), [text](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/text-ads-integrations?view=li-lms-2026-02), [document](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/document-ads?view=li-lms-2026-02), or a reference to [InMail Content](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/message-ads-integrations?view=li-lms-2026-02) or post ([image](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/image-ads-integrations?view=li-lms-2026-02), [video](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/create-and-manage-video?view=li-lms-2026-02), [article](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/article-ads-integrations?view=li-lms-2026-02), [carousel](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/carousel-ads-integrations?view=li-lms-2026-02)). Content can also be extended and specified as inline content instead of an URN. A reference must be a adInMailContent{id}, share{id}, or ugcPost{id}. `Note`: For API Versions starting from 202505 and later, the content may also be an [EventAd](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#eventad), an advertisement of an [event](https://learn.microsoft.com/en-us/linkedin/marketing/event-management/events?view=li-lms-2026-02) on LinkedIn. `Note`: For API Versions starting from 202507 and later, the content may also be an [ThirdPartyVastTagVideoAd](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/version/vast-tag-video-ads-api?view=li-lms-2026-02).|
|createdAt|No|Time|Creation time|
|createdBy|No|Person URN|Entity (e.g., a person URN) that developed the creative|
|id|No|Sponsored creative URN|Unique ID for a creative (e.g.,SponsoredCreativeUrn). Read-only|
|inlineContent|Required if action is createInline|Post|Inline content sponsored in the creative such as ugcPost in order to reduce the number of user calls.|
|intendedStatus|No|ENUM|Creative user intended status. The creative intended status is set independently from parent entity status, but parent entity status overrides creative intended status in effect. For example, parent entity status may be PAUSED while creative status is ACTIVE, in which case the creative's effective status is PAUSED, and not served.- ACTIVE - Creative development is complete and the creative is available for review and can be served.<br>- PAUSED - Creative development is complete and the creative is current, but should temporarily not be served.<br>- DRAFT - Creative development is incomplete and may still be edited.<br>- ARCHIVED - Creative development is complete, but creative shouldn't be served and should be separated from non-archived creatives in any UI.<br>- CANCELED - The creative will be hidden when querying all creatives under a campaign and canceled creatives will be retrievable if the underlying posts are still valid/available.<br>- PENDING_DELETION - Denotes that the creative has been requested to be deleted that's currently pending.<br>- REMOVED - Denotes that the creative was deleted, but must remain fetchable due to the existence of performance data.|
|isServing|No|boolean|This indicates whether the creative is currently being served or not. This field is read-only.|
|lastModifiedAt|No|Time|Time at which the creative was last modified in milliseconds since epoch.|
|lastModifiedBy|No|Person URN|The entity (e.g., person URN) who modified the creative|
|[leadgenCallToAction](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#leadgencreativecalltoaction)|Required if campaign objective is `LEAD_GENERATION`|LeadgenCreativeCallToAction|The field is needed for call to action. This currently only applies if the campaign objective is LEAD_GENERATION.|
|review|No|CreativeReview|Creative review status. The review status can't be set/updated via the API but is started when the creative is activated (i.e., moves from draft state to active state). Hence, the review is absent (null) when the creative is in DRAFT state. Read-only.|
|[servingHoldReasons](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#servingholdreasons)|No|servingHoldReasons|Array that contains all the reasons why the creative is not serving. In the case a creative is being served, this field will be null and not present in the response.|
|name|No|string|The name of the creative that can be set by advertiser; primarily used to make it easier to reference a Creative and to recall its purpose.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#creativereview)

### CreativeReview

|Field Name|Required|Type|Description|
|---|---|---|---|
|status|Yes|ENUM|- PENDING - Creative is pending review and not serving.<br>- APPROVED - Creative is approved for serving. It includes Creative that has been preapproved or auto approved by content model.<br>- REJECTED - Creative is rejected. It includes the Creative that has been auto rejected by content model.<br>- NEEDS_REVIEW - Creative has been rejected by content model or policy checker or returned by fallback case that auto approval didn't make any decision.|
|rejectionReasons|No|Array[]|An array of reasons for rejecting creatives. For more details, refer to the [RejectionReason list](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#ad-creative-rejection-reasons).|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#servingholdreasons)

### servingHoldReasons

|Name|Description|
|---|---|
|STOPPED|Stopped by the advertiser.|
|UNDER_REVIEW|Creative can't be served because it hasn't been reviewed.|
|REJECTED|Creative can't be served because it was reviewed and rejected.|
|FORM_HOLD|Creative can't be served because it's associated with a form and is currently not servable.|
|PROCESSING|Creative is being processed.|
|PROCESSING_FAILED|Creative failed processing.|
|REFERRED_CONTENT_QUALITY_HOLD|Creative can't be served because it's associated with an non-quality entity (e.g., UGC/vector asset).|
|JOB_POSTING_ON_HOLD|Single job ad, job state is in review or suspended or job posting is no longer available to members. The associated creatives should be held for serving.|
|JOB_POSTING_INVALID|Single job ad, if job state is closed, deleted, or the member can not apply to the job, the single job ad is not served.|
|CAMPAIGN_STOPPED|Campaign is currently not servable for reasons other than billing information, budgetary constraints, or termination dates. For example, a campaign is STOPPED if it has been PAUSED by the user.|
|ACCOUNT_TOTAL_BUDGET_HOLD|Parent account total budget has been reached.|
|ACCOUNT_END_DATE_HOLD|Parent account end date has been reached.|
|CAMPAIGN_START_DATE_HOLD|Campaign start date is in the future.|
|CAMPAIGN_END_DATE_HOLD|Campaign end date has been reached.|
|CAMPAIGN_TOTAL_BUDGET_HOLD|Campaign total budget has been reached.|
|CAMPAIGN_AUDIENCE_COUNT_HOLD|Campaign is on hold because it has an audience count lower than the threshold.|
|CAMPAIGN_GROUP_START_DATE_HOLD|Campaign group start date is in the future.|
|CAMPAIGN_GROUP_END_DATE_HOLD|Campaign group end date is in the past.|
|CAMPAIGN_GROUP_TOTAL_BUDGET_HOLD|Campaign group total budget has been reached.|
|CAMPAIGN_GROUP_STATUS_HOLD|Campaign group status is on hold.|
|ACCOUNT_SERVING_HOLD|Parent account is on hold and not eligible for serving|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#leadgencreativecalltoaction)

### LeadgenCreativeCallToAction

|Field Name|Required|Type|Description|
|---|---|---|---|
|destination|Yes|AdFormUrn|This form is a target destination for the callToAction button. It can only be modified when the creative is in DRAFT status. It is immutable once it's set for a creative once it transition to any non-draft intended status.|
|label|Yes|CallToActionLabel|Label for the CallToAction button.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#call-to-action-label-types)

#### Call to Action Label Types

|Type|Description|
|---|---|
|APPLY|Call To Action button on the creative shows 'Apply now'.|
|DOWNLOAD|Call To Action button on the creative shows 'Download'.|
|VIEW_QUOTE|Call To Action button on the creative shows 'Get Quote'.|
|LEARN_MORE|Call To Action button on the creative shows 'Learn More'.|
|SIGN_UP|Call To Action button on the creative shows 'Sign Up'.|
|SUBSCRIBE|Call To Action button on the creative shows 'Subscribe'.|
|REGISTER|Call To Action button on the creative shows 'Register'.|
|REQUEST_DEMO|Call To Action button on the creative shows 'Request Demo'.|
|JOIN|Call To Action button on the creative shows 'Join'.|
|ATTEND|Call To Action button on the creative shows 'Attend'.|
|UNLOCK_FULL_DOCUMENT|Call To Action button on the creative shows 'Unlock Full Document'.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#eventad)

### EventAd

| Field Name                | Required on Create | Read Only | Type                                                              | Default | Description                                                                                                                                                                                                                                                                                                                                       |
| ------------------------- | ------------------ | --------- | ----------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| post                      | Yes                | Yes       | UserGeneratedContentPostUrn                                       |         | URN identifying the sponsored user generated content post.                                                                                                                                                                                                                                                                                        |
| directSponsoredContent    | No                 | Yes       | boolean                                                           | false   | Indicates whether the creative is direct sponsored content or not. Direct sponsored content allows an advertiser to sponsor content without first publishing the content on the Company Page or the Showcase Page, while non-direct sponsored content publish the content on the Company Page or the Showcase Page before sponsoring the content. |
| event                     | Yes                | Yes       | EventUrn                                                          |         | The LinkedIn event URN associated with this creative.                                                                                                                                                                                                                                                                                             |
| preEventRegistrationImage | No                 | Yes       | DigitalmediaAssetUrn                                              |         | Image shown to users who haven't registered for event yet.                                                                                                                                                                                                                                                                                        |
| hidePreviewVideo          | No                 | No        | boolean                                                           | false   | This flag will indicate whether the preview should be hidden or not. Applicable only to live video events to which a lead gen form is attached.                                                                                                                                                                                                   |
| contentAuthor             | No                 | Yes       | PersonUrn or OrganizationUrn](../pages-profiles/organizations.md) |         | Author of the content.                                                                                                                                                                                                                                                                                                                            |


## Get a Creative

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/mcb3iqo/creative-management)

To obtain details provide the Creative URN in encoded format as shown in the following example.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#sample-request-2)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_4_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_4_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/520866471/creatives/urn%3Ali%3AsponsoredCreative%3A120491345
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#sample-response-3)

#### Sample Response

JSON

```

{
  "createdAt": 1624249280000,
  "servingHoldReasons": [
    "STOPPED",
    "CAMPAIGN_STOPPED",
    "ACCOUNT_SERVING_HOLD",
    "CAMPAIGN_GROUP_STATUS_HOLD"
  ],
  "lastModifiedAt": 1624249280000,
  "isTest": false,
  "createdBy": "urn:li:person:rboDhL7Xsf",
  "isServing": false,
  "name": "the sample creative name",
  "lastModifiedBy": "urn:li:person:rboDhL7Xsf",
  "campaign": "urn:li:sponsoredCampaign:360035215",
  "id": "urn:li:sponsoredCreative:119962155",
  "intendedStatus": "DRAFT",
  "name": "Test Creative 1",
  "account": "urn:li:sponsoredAccount:520866471",
  "content": {
    "reference": "urn:li:ugcPost:6778045555198214144"
  }
}

```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#search-for-creatives)

## Search For Creatives

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/mcb3iqo/creative-management)

 Note

From 202401 version and above, we have moved from index based pagination to cursor based pagination for our search APIs.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#cursor-based-pagination-for-search-apis)

### Cursor based Pagination for search APIs

The creatives API implements cursor based pagination using the pageSize and pageToken parameters for search method. The max allowed pageSize is 100.

- pageSize governs the number of requested entities
- pageToken is used to get the next set of results.
    - nextPageToken is returned in metadata field of the search response.
    - This should be passed in pageToken query parameter in the request to get the next page of results.

Search for creative content in order to get a collection of creatives matching your search parameters. The Creative API currently supports search by `creative id`, `campaign`, `content reference`, `intendedStatus`, `leadgenCreativeCallToActionDestinations` and test fields. The values within each field are displayed with 'or' (ORed) and values across fields are displayed with 'and' (ANDed).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#sample-request-3)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_5_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_5_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/{adAccountId}/creatives?campaigns=List(id1,id2,id3)&contentReferences=List(id1,id2,id3)&creatives=List(id1,id2,id3)&intendedStatuses=List(ARCHIVED,CANCELED)&isTestAccount=true&isTotalIncluded=false&leadgenCreativeCallToActionDestinations=List()&q=criteria&sortOrder=ASCENDING
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#parameters)

#### Parameters

|Field Name|Required|Description|
|---|---|---|
|campaigns|sponsoredCampaignUrn[] default=[]|Search values associated with creative sponsored campaign account|
|contentReferences|URN[] default=[]|Search values associated with creative content reference, can be share URN, or ugcPosts URN|
|Creatives|sponsoredCreativeUrn[] default=[]|Search values associated with creative ID|
|intendedStatuses|IntendedStatus[] default=[]|Search values associated with creative intendedStatus|
|isTestAccount|optional boolean|Search values associated with creative isTest flag. True returns creatives only under test accounts. False returns creatives only under non-test accounts. Setting this to null returns creatives regardless of the account being test or non-test|
|leadgenCreativeCallToActionDestinations|adFormUrn[] default=[]|Search values associated with the creative leadgenCallToAction destination|
|sortOrder|SortOrder default=ASCENDING|Sort mode by creative ID for matching records|
|pageSize|no|Specifies the number of entities to be returned. The default is 100.|
|pageToken|no|Unique key representing the last entity of the response. This is to be used to fetch the next set of entities. If less than pageSize entities are returned in the current response, pageToken will be null|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#sample-request-4)

#### Sample Request

The following example describes a search for all creatives associated with a list of creative IDs. The `id` results are in ascending order.

The header X-RestLi-Method must be included in the request and set to `FINDER`.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_6_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_6_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/520866471/creatives?creatives=List(urn%3Ali%3AsponsoredCreative%3A119962155)&q=criteria&sortOrder=ASCENDING
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#sample-response-4)

#### Sample Response

JSON

```
{
  "metadata": {
    "nextPageToken": "DgGerr1iVQreCJVjZDOW_grcp63nueBDipsS4DJpvJo"
  },
  "elements": [
    {
      "createdAt": 1624249280000,
      "servingHoldReasons": [
        "STOPPED",
        "CAMPAIGN_STOPPED",
        "ACCOUNT_SERVING_HOLD",
        "CAMPAIGN_GROUP_STATUS_HOLD"
      ],
      "lastModifiedAt": 1624249280000,
      "isTest": false,
      "createdBy": "urn:li:person:rboDhL7Xsf",
      "isServing": false,
      "lastModifiedBy": "urn:li:person:rboDhL7Xsf",
      "campaign": "urn:li:sponsoredCampaign:360035215",
      "id": "urn:li:sponsoredCreative:119962155",
      "intendedStatus": "DRAFT",
      "account": "urn:li:sponsoredAccount:520866471",
      "content": {
        "reference": "urn:li:share:6778045555198214144"
      }
    }
  ]
}
```

API Call to get the next set of results would use the nextPageToken passed in the response above.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_7_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#tabpanel_7_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAccounts/520866471/creatives?creatives=List(urn%3Ali%3AsponsoredCreative%3A119962155)&q=criteria&sortOrder=ASCENDING&pageToken=DgGerr1iVQreCJVjZDOW_grcp63nueBDipsS4DJpvJo
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/account-structure/create-and-manage-creatives?view=li-lms-2026-02&tabs=http#update-a-creative)
# Ad Targeting

 Warning

**Deprecation Notice:** The Marketing Version 202502 (Marketing February 2025) has been sunset. We recommend that you migrate to the latest [versioned APIs](https://learn.microsoft.com/en-us/linkedin/marketing/versioning?view=li-lms-2026-02) to avoid disruptions. For information on all the supported versions, refer to the [migrations](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/migrations?view=li-lms-2026-02#api-migration-status) documentation. If you haven’t yet migrated and have questions, submit a request on the [LinkedIn Developer Support Portal](https://linkedin.zendesk.com/hc/en-us).

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

LinkedIn's Ad Targeting API enables advertisers to better control which audiences see their ads. These controls include a variety of member professional demographics in the LinkedIn platform. Targeting is set at the campaign level, and applies to all creatives associated with that campaign.

The two core concepts for targeting are facets and entities.

Facets are high-level categories of the types of targeting available to you. Facets contain multiple entities which are the specific professional demographic values within that facet.

For example, Industries is a facet. Specific industries such as Computer Software, Biotechnology, and Telecommunications are entities within the Industries facet.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#permissions)

### Permissions

Any application approved for the LinkedIn Marketing API Program can make these API calls using any 3-legged access token. No additional permissions need to be requested during the OAuth flow.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#targeting-discrimination-notice)

### Targeting Discrimination Notice

Applications utilizing LinkedIn's targeting capabilities are required to display a notice in their user interface notifying advertisers that they can't use LinkedIn to discriminate against members based on personal characteristics. The notice should include the following text:

LinkedIn tools may not be used to discriminate based on personal characteristics like gender, age, race, or ethnicity. [Learn more](https://www.linkedin.com/help/lms/answer/86856).

To learn more about targeting in general on LinkedIn, see [Targeting Options](https://www.linkedin.com/help/linkedin/answer/a424655/targeting-options-and-best-practices-for-linkedin-advertisements?lang=en)and [Best Practices for LinkedIn Advertisements](https://www.linkedin.cn/help/lms/answer/a417950?trk=hc-articlePage-peopleAlsoViewed).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#ad-targeting-facets)

## Ad Targeting Facets

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

Facets are high-level categories of the types of targeting available to you. Use facets to narrow down your intended audience. Refer to [Targeting Criteria Facet URNs](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/targeting-criteria-facet-urns?view=li-lms-2026-02) for the list of available facets and their URNs.

The `adTargetingFacets` API returns available targeting facets.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request)

#### Sample Request

To add new fields or enums to an existing schema:

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_1_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_1_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingFacets
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response)

#### Sample Response

The response returns facets available to you for targeting. Each targeting type contains the name of the facet, the type, and Finder methods to get more information on the type and values.

To learn more, see the [Ad Targeting Facets API](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/adtargetingfacets?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext).

JSON

```
{ 
   "elements":[ 
      {
         "facetName":"genders",
         "availableEntityFinders":[ 
            "AD_TARGETING_FACET"
          ],
         "entityTypes":[ 
            "GENDER"
          ],
         "adTargetingFacetUrn":"urn:li:adTargetingFacet:genders"
       },
      {
         "facetName":"industries",
         "availableEntityFinders":[ 
            "AD_TARGETING_FACET",
            "TYPEAHEAD",
            "SIMILAR_ENTITIES"
          ],
         "entityTypes":[ 
            "INDUSTRY"
          ],
         "adTargetingFacetUrn":"urn:li:adTargetingFacet:industries"
       },
      ... some facets omitted ...
      { 
         "facetName":"memberBehaviors",
         "availableEntityFinders":[ 
            "AD_TARGETING_FACET",
            "TYPEAHEAD"
          ],
         "entityTypes":[ 
            "MEMBER_BEHAVIOR"
          ],
         "adTargetingFacetUrn":"urn:li:adTargetingFacet:memberBehaviors"
       },
      { 
         "facetName":"growthRate",
         "availableEntityFinders":[ 
            "AD_TARGETING_FACET",
            "TYPEAHEAD"
          ],
         "entityTypes":[ 
            "FIRMOGRAPHIC"
          ],
         "adTargetingFacetUrn":"urn:li:adTargetingFacet:growthRate"
       },
      { 
         "facetName":"companyCategory",
         "availableEntityFinders":[ 
            "AD_TARGETING_FACET",
            "TYPEAHEAD"
          ],
         "entityTypes":[ 
            "FIRMOGRAPHIC"
          ],
         "adTargetingFacetUrn":"urn:li:adTargetingFacet:companyCategory"
       }
    ]
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#ad-targeting-entities)

## Ad Targeting Entities

Once you've identified the facet type(s) you'd like to target, you can fetch their entity values.

Use the `adTargetingEntities` API to fetch available options for each facet type. To learn more, see [Ad Targeting Entities](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/adtargetingentities?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontex).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#find-entities-by-facet)

### Find Entities by Facet

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

This method returns targeting entities contained within a given targeting facet. For example, passing in the industries targeting facet will return names and URNs for all the industry targeting entities.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_2_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_2_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=adTargetingFacet&facet={encoded adTargetingFacet URN}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#parameters)

#### Parameters

|Field Name|Required|Type|Description|
|---|---|---|---|
|q|Yes|String|This field should always be `adTargetingFacet` for this method.|
|facet|Yes|adTargetingFacet URN|Targeting facet that results should be returned for.|
|locale.language|No|String|A lowercase two-letter language code as defined by [ISO-639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Defaults to "en" if no value is provided.|
|locale.country|No|String|An uppercase two-letter country code as defined by [ISO-3166](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Defaults to "US" if no value is provided.|
|queryVersion|No|String|This field should always be `QUERY_USES_VALUES`.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-1)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=adTargetingFacet&queryVersion=QUERY_USES_URNS&facet=urn%3Ali%3AadTargetingFacet%3Aseniorities&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-1)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "urn": "urn:li:seniority:1",
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Unpaid"
        },
        {
            "urn": "urn:li:seniority:10",
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Owner"
        },
        {
            "urn": "urn:li:seniority:2",
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Training"
        },
        {
            "urn": "urn:li:seniority:3",
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Entry"
        },
        {
            "urn": "urn:li:seniority:4",
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Senior"
        },
    ..
    ]
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#ad-targeting-entities-for-member-behaviors)

#### Ad Targeting Entities for Member Behaviors

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_4_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_4_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=adTargetingFacet&facet=urn%3Ali%3AadTargetingFacet%3AmemberBehaviors&queryVersion=QUERY_USES_URNS&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-2)

#### Sample Response

JSON

```
{
    "elements": [
       {
            "urn": "urn:li:memberBehavior:2",
            "facetUrn": "urn:li:adTargetingFacet:memberBehaviors",
            "name": "Mobile Users"
        },
        {
            "urn": "urn:li:memberBehavior:3",
            "facetUrn": "urn:li:adTargetingFacet:memberBehaviors",
            "name": "iPhone Users",
        },
        ... Some entities omitted ...
        {
            "urn": "urn:li:memberBehavior:13",
            "facetUrn": "urn:li:adTargetingFacet:memberBehaviors",
            "name": "Open to Education",
        },
        {
            "urn": "urn:li:memberBehavior:14",
            "facetUrn": "urn:li:adTargetingFacet:memberBehaviors",
            "name": "Frequent Contributor",
        }
    ],
    "paging": {
        "count": 2147483647,
        "start": 0,
        "links": []
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#ad-targeting-entities-for-company-growth-rate-and-category)

### Ad Targeting Entities for Company Growth Rate and Category

LinkedIn now enables advertisers to include company growth rate and company category to target LinkedIn members by.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-2)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_5_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_5_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?facet=urn%3Ali%3AadTargetingFacet%3AcompanyCategory&q=adTargetingFacet&queryVersion=QUERY_USES_URNS&totals=false
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-3)

#### Sample Response

JSON

```
  {
    "elements": [
        {
            "urn": "urn:li:organizationRankingList:1",
            "facetUrn": "urn:li:adTargetingFacet:companyCategory",
            "name": "Fortune Global 500",
        },
     // ... Some entities omitted ...
        {
             "urn": "urn:li:organizationRankingList:3",
            "facetUrn": "urn:li:adTargetingFacet:companyCategory",
            "name": "Forbes World's Most Innovative Companies",
        }
    ],
    "paging": {
        "count": 2147483647,
        "start": 0,
        "links": []
    }
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#find-entities-by-similar-entities)

### Find Entities by Similar Entities

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

This method returns targeting entities that are similar to a given targeting entity. For example, passing in the employers targeting facet and an organization URN for a university would return name and URNs of similar employers. In this case, the similar employers would be other universities.

The number of entities per facet is capped to 100 for nearly all facets. The exceptions are employers, employersPast, employersAll, geos, and profileGeos which are capped to 200. To target a larger audience, see [Audiences](https://learn.microsoft.com/en-us/linkedin/marketing/matched-audiences/matched-audiences?view=li-lms-2026-02).

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_6_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_6_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=similarEntities&facet={facetURN}&entities=List({encoded URN1},{encoded URN2})
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#parameters-1)

#### Parameters

|Field Name|Required|Type|Description|
|---|---|---|---|
|q|Yes|String|This field should always be `similarEntities` for this method.|
|facet|Yes|adTargetingFacet URN|Targeting facet that results should be returned for.|
|entities|Yes|Array of URNs|URNs of the entities that will be use to retrieve similar entities for.|
|entityType|No|String|Enum to restrict results to only contain data that matches type requested. Possible values:<br><br>- AGE<br>- COMPANY<br>- COMPANY_SIZE<br>- DEGREE<br>- FIELD_OF_STUDY<br>- FUNCTION<br>- GENDER<br>- GROUP<br>- INDUSTRY<br>- LOCALE<br>- SCHOOL<br>- SENIORITY<br>- SKILL<br>- TITLE<br>- YEARS_OF_EXPERIENCE|
|locale.language|No|String|A lowercase two-letter language code as defined by [ISO-639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Defaults to "en" if no value is provided.|
|locale.country|No|String|An uppercase two-letter country code as defined by [ISO-3166](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Defaults to "US" if no value is provided.|
|queryVersion|No|String|This field should always be `QUERY_USES_URNS`.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-3)

#### Sample Request

This example shows how to discover similar employers by passing in an organization URN.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_7_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_7_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=similarEntities&facet=urn%3Ali%3AadTargetingFacet%3Aemployers&queryVersion=QUERY_USES_URNS&entities=List(urn%3Ali%3Aorganization%3A1003)&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-4)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "urn": "urn:li:organization:163361",
            "facetUrn": "urn:li:adTargetingFacet:employers",
            "name": "DataMirror"
        },
        {
            "urn": "urn:li:organization:1666",
            "facetUrn": "urn:li:adTargetingFacet:employers",
            "name": "Intuit"
        },
        {
            "urn": "urn:li:organization:10715",
            "facetUrn": "urn:li:adTargetingFacet:employers",
            "name": "Lexmark Enterprise Software"
        },
        {
            "urn": "urn:li:organization:21867",
            "facetUrn": "urn:li:adTargetingFacet:employers",
            "name": "eClinicalWorks"
        }
    ],
    "paging": {
        "total": 48,
        "count": 2147483647,
        "start": 0,
        "links": []
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#find-entities-by-typeahead)

### Find Entities by Typeahead

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

This method allows search of targeting entities within a given targeting facet.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_8_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_8_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=typeahead&facet={encoded adTargetingFacet URN}&query={Search Query}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#parameters-2)

#### Parameters

|Field Name|Required|Type|Description|
|---|---|---|---|
|q|Yes|String|This field should always be `TYPEAHEAD` for this method.|
|facet|Yes|adTargetingFacet URN|Targeting facet that results should be returned for.|
|query|Yes|String|String of partial text to be used for matching with.|
|entityType|No|String|Enum to restrict results to only contain data that matches type requested. Possible values:<br><br>- AGE<br>- COMPANY<br>- COMPANY_SIZE<br>- DEGREE<br>- FIELD_OF_STUDY<br>- FUNCTION<br>- GENDER<br>- GROUP<br>- INDUSTRY<br>- INTEREST<br>- LOCALE<br>- SCHOOL<br>- SENIORITY<br>- SKILL<br>- TITLE<br>- YEARS_OF_EXPERIENCE<br>- MEMBER_BEHAVIOR|
|locale.language|No|String|A lowercase two-letter language code as defined by [ISO-639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Defaults to "en" if no value is provided.|
|locale.country|No|String|An uppercase two-letter country code as defined by [ISO-3166](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Defaults to "US" if no value is provided.|
|queryVersion|No|String|This field should always be `QUERY_USES_URNS`.|
|useCase|No|String|Enum to indicate whether filtering targeting entities for a specific use case is needed. Possible values:<br><br>- CONNECTED_TELEVISION_ONLY_CAMPAIGN<br><br>`Note`: Applicable only from API versions 202503 and later.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-get-fields-of-study-entities-for-economics)

#### Sample Request: GET Fields of Study Entities for 'Economics'

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_9_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_9_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=typeahead&entityType=FIELD_OF_STUDY&queryVersion=QUERY_USES_URNS&facet=urn%3Ali%3AadTargetingFacet%3AfieldsOfStudy&query=econ&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-5)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "urn": "urn:li:fieldOfStudy:100990",
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "Economics"
        },
        {
            "urn": "urn:li:fieldOfStudy:101438",
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "Business/Managerial Economics"
        },
        {
            "urn": "urn:li:fieldOfStudy:100994",
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "International Economics"
        },
        {
            "urn": "urn:li:fieldOfStudy:100993",
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "Development Economics and International Development"
        },
        {
            "urn": "urn:li:fieldOfStudy:100991",
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "Applied Economics"
        },
    ..
    ]
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-get-locations-entities-for-location-africa)

#### Sample Request: GET Locations Entities for Location 'Africa'

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_10_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_10_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=typeahead&queryVersion=QUERY_USES_URNS&facet=urn%3Ali%3AadTargetingFacet%3Alocations&query=afric&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-6)

#### Sample Response

JSON

```
{
    "elements": [
       {
            "urn": "urn:li:geo:103537801",
            "facetUrn": "urn:li:adTargetingFacet:locations",
            "name": "Africa"
        },
        {
        
            "urn": "urn:li:geo:104035573",
            "facetUrn": "urn:li:adTargetingFacet:locations",
            "name": "South Africa"
        },
    ]
    
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#find-entities-by-urns)

### Find Entities by URNs

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/u3xn48e/ads-targeting)

Get the metadata and value information for a collection of URNs.

 Note

All requests are represented in protocol 2.0.0 and require the following header: X-Restli-Protocol-Version: 2.0.0

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_11_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_11_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=urns&urns={URN}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#parameters-3)

#### Parameters

|Field Name|Required|Type|Description|
|---|---|---|---|
|q|Yes|String|This field should always be `urns` for this method.|
|urns|Yes|Array of URNs|List of URNs requesting metadata for.|
|locale.language|No|String|A lowercase two-letter language code as defined by [ISO-639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Defaults to "en" if no value is provided.|
|locale.country|No|String|An uppercase two-letter country code as defined by [ISO-3166](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Defaults to "US" if no value is provided.|
|queryVersion|No|String|This field should always be `QUERY_USES_URNS`.|
|fetchType|No|String|Determines how much of an URN's descendant tree is returned.<br><br>- SINGLE_NODE: Default value. Resolve and return only the entities explicitly requested with no descendants.<br>- LAZY: Resolve and return all entities except those with a large taxonomy size. Supported when passing a single URN value only.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-to-get-field-of-study-names)

#### Sample Request to Get Field of Study Names

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_12_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_12_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=urns&urns=List(urn%3Ali%3AfieldOfStudy%3A100990,urn%3Ali%3Aorganization%3A1035,urn%3Ali%3Aseniority%3A9)&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-7)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "facetUrn": "urn:li:adTargetingFacet:fieldsOfStudy",
            "name": "Economics",
            "urn": "urn:li:fieldOfStudy:100990"
        },
        {
            "facetUrn": "urn:li:adTargetingFacet:employersPast",
            "name": "Microsoft",
            "urn": "urn:li:organization:1035"
        },
        {
            "facetUrn": "urn:li:adTargetingFacet:seniorities",
            "name": "Partner",
            "urn": "urn:li:seniority:9"
        }
    ],
    "paging": {
        "count": 2147483647,
        "links": [],
        "start": 0
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-request-to-get-locations)

#### Sample Request to Get Locations

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_13_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#tabpanel_13_curl)

HTTP

```
GET https://api.linkedin.com/rest/adTargetingEntities?q=urns&queryVersion=QUERY_USES_URNS&urns=List(urn%3Ali%3Ageo%3A102095887,urn%3Ali%3Ageo%3A101857797)&locale=(language:en,country:US)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#sample-response-8)

#### Sample Response

JSON

```
{
  "elements": [
    {
      "urn": "urn:li:geo:102095887",
      "facetUrn": "urn:li:adTargetingFacet:locations",
      "name": "California, United States"
    },
    {
      "urn": "urn:li:geo:101857797",
      "facetUrn": "urn:li:adTargetingFacet:locations",
      "name": "Sacramento, California, United States"
    }
  ],
  "paging": {
    "count": 2147483647,
    "links": [],
    "start": 0
  }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#discovering-targeting-entities)

### Discovering Targeting Entities

Following table shows a list of all the targeting facets and the corresponding endpoint to retrieve list of entities for a given targeting facet.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/ads-targeting?view=li-lms-2026-02&tabs=http#types-of-finder)

#### Types of Finder

- adTargetingFacet returns all the targeting entities for a given facet.
- typeahead only returns targeting entities for a given targeting facet search query.
- similarEntities returns similar targeting entities for a given targeting entity.

|AdTargetingFacets|Supported Finder|Recommended Finder|
|---|---|---|
|urn:li:adTargetingFacet:genders|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:industries|adTargetingFacet, typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:jobFunctions|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:seniorities|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:ageRanges|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:locations|typeahead only after Bing Geo Migration|typeahead|
|urn:li:adTargetingFacet:profileLocations|typeahead only after Bing Geo Migration|typeahead|
|urn:li:adTargetingFacet:staffCountRanges|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:employers|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:employersPast|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:employersAll|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:groups|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:titles|adTargetingFacet, typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:titlesPast|adTargetingFacet, typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:titlesAll|adTargetingFacet, typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:skills|adTargetingFacet, typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:schools|typeahead|typeahead|
|urn:li:adTargetingFacet:interfaceLocales|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:followedCompanies|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:degrees|adTargetingFacet, typeahead|typeahead|
|urn:li:adTargetingFacet:fieldsOfStudy|adTargetingFacet, typeahead|typeahead|
|urn:li:adTargetingFacet:yearsOfExperienceRanges|adTargetingFacet|adTargetingFacet|
|urn:li:adTargetingFacet:firstDegreeConnectionCompanies|typeahead, similarEntities|typeahead|
|urn:li:adTargetingFacet:audienceMatchingSegments|N/A|N/A|
|urn:li:adTargetingFacet:dynamicSegments|N/A|N/A|
|urn:li:adTargetingFacet:interests|adTargetingFacet, typeahead|typeahead|
|urn:li:adTargetingFacet:memberBehaviors|adTargetingFacet, typeahead|adTargetingFacet|
|urn:li:adTargetingFacet:companyCategory|adTargetingFacet, typeahead|adTargetingFacet|
|urn:li:adTargetingFacet:growthRate|adTargetingFacet, typeahead|adTargetingFacet|
|urn:li:adTargetingFacet:revenue|adTargetingFacet, typeahead|adTargetingFacet|

# Audience Counts
## Schema

| Field Name                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Description                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| active                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Active audience count for the given targeting criteria. Active audience includes members that are more likely to visit LinkedIn sites.                                                                                                                          |
| ## Find Count by CriteriaV2<br><br>[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/e90003l/audience-counts)<br><br>This finder gets the audience count for a given set of targeting criteria. For more information refer to [Targeting Criteria](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/targeting-criteria?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext).<br><br>The parameter `q=targetingCriteriaV2` is always required as it represents the Finder `targetingCriteriaV2` request.<br><br>All API requests are represented in protocol 2.0.0 and require the header `X-Restli-Protocol-Version: 2.0.0`.<br><br>Restli 2.0 requires URNs in query params to be URL encoded. For example, `urn:li:skill:17` would become `urn%3Ali%3Askill%3A17`.<br><br>Note that Postman or similar API tools may not support these types of calls. Testing with curl is recommended if you encounter a 400 error with message `Invalid query parameters passed to request`.total | Total audience count for the given targeting criteria. To protect member privacy, this value is 0 when the audience size is less than 300. The total is a rounded approximation, and the degree of approximation depends upon the size of the audience segment. |



Calls to this endpoint are structured as follows:

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_1_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_1_curl)

HTTP

```
GET https://api.linkedin.com/rest/audienceCounts?q=targetingCriteriaV2&targetingCriteria=(include:(and:List((or:({encoded facet_URN_1}:List({encoded facet_URN_1_value_1}, {encoded facet_URN_1_value_2}))),(or:({encoded facet_URN_2}:List({encoded facet_URN_2_value_1},{encoded facet_URN_2_value_2}))))))
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#parameters)

#### Parameters

|Field Name|Required|Type|Description|
|---|---|---|---|
|q|This field should always be `targetingCriteriaV2`|String|Yes|
|targetingCriteria|Yes|[targetingCriteria](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/targeting-criteria?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext) object|Specifies the targeting criteria that the member should match.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#sample-request)

### Sample Request

The following shows a sample request forecasting the audience count for members living in North America and skill type “Engineering”.

Any URNs included in the parameters must be URL encoded. An unencoded sample request has also been provided for readability.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#unencoded-sample-request)

#### Unencoded Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_2_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_2_curl)

HTTP

```
GET https://api.linkedin.com/rest/audienceCounts?q=targetingCriteriaV2&targetingCriteria=(include:(and:List((or:(urn:li:adTargetingFacet:locations:List(urn:li:geo:102221843))),(or:(urn:li:adTargetingFacet:skills:List(urn:li:skill:17))))))
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#encoded-sample-request)

#### Encoded Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/audienceCounts?q=targetingCriteriaV2&targetingCriteria=(include:(and:List((or:(urn%3Ali%3AadTargetingFacet%3Alocations:List(urn%3Ali%3Ageo%3A102221843))),(or:(urn%3Ali%3AadTargetingFacet%3Askills:List(urn%3Ali%3Askill%3A17))))))
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/advertising-targeting/audience-counts?view=li-lms-2026-02&tabs=http#sample-response)

### Sample Response

The API returns a list of `AudienceCount` results based on `targetingCriteria` parameters.

JSON

```
{
    "elements": [
        {
            "active": 0,
            "total": 25312600
        }
    ],
    "paging": {
        "count": 10,
        "links": [],
        "start": 0
    }
}
```

# Reporting
The LinkedIn Reporting APIs provide key insights on performance such as clicks, impressions, ad spend and professional demographics information such as metrics by professional demographic values at the `account`, `campaign` or `creative` levels.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#permissions)

### Permissions

|Permission|Description|
|---|---|
|r_ads_reporting|Retrieve reporting for advertising accounts.|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#ad-analytics)

## Ad Analytics

The `adAnalytics` endpoint supports three finder methods:

- [Analytics](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#analytics-finder): Use when grouping by one element (known as a pivot).
- [Statistics](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#statistics-finder): Use when grouping by up to three elements.
- [AttributedRevenueMetrics](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#attributed-revenue-metrics-finder): Use to request revenue attribution metrics.

 Note

- The `adAnalytics` endpoint currently does not support pagination.
- Some metrics are not available with professional demographic pivots. These are noted in the [metrics available](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#metrics-available) table.
- An empty response is returned if there's no activity to report or if you don't have read access to the requested advertising data.
- Requests to `adAnalytics` can have a long list of query parameters causing them to exceed max request URL lengths. If you encounter a 414 error or expect to have long request URLs, refer to the [query tunneling guide](https://learn.microsoft.com/en-us/linkedin/shared/references/migrations/query-tunneling-migration?view=li-lms-2026-02) for how to adjust your calls.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#retention)

### Retention

The retention period for data depends on the type of request. Following are the types of requests and their retention periods:

- Requests for performance data (for example, by account, campaign, or creative) are retained for ten (10) years.
- Professional demographics data (for example, by member title, job function, or seniority) is retained for two (2) years.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#restrictions)

### Restrictions

The following restrictions apply based on your query parameters.

- An empty response is returned if there's no activity to report or if you don't have read access to the requested advertising data.
- Pagination is not supported.
- Some metrics are not available with specific pivots (e.g. conversion or professional demographics pivots). These are noted in the [metrics available](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#metrics-available) table.
- When `timeGranularity=ALL`, if either the start or end date of a request range is outside the 6-month daily retention period, the dates are automatically rounded to month boundaries, and the entire month's data is included in the response. Example: If a request is made on 8/1/2021 with `dateRange.start = 1/15/2021` and `dateRange.end = 7/15/2021`, then `dateRange.start` is automatically adjusted to 1/1/2021. This is because 1/15/2021 is outside of a 6 month retention period for daily data, whereas monthly data for January is still within the 2 year retention period.
- Response is limited to 15,000 elements.
- Professional Demographic pivots only support the top 100 professional demographic values for each creative for each day. Example: If a creative is shown to members with 1,000 different titles, a query for the impressions for that creative with a `MEMBER_JOB_TITLE` pivot returns the 100 titles with the most impressions for that creative for that day.
- Professional Demographic values are not returned for ads receiving engagement from too few members.
- Professional Demographic pivots have a minimum threshold of 3 events. Professional Demographic values with less than 3 events are dropped from the query results.
- Professional Demographic pivots don't support carousel metrics.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#delays)

### Delays

Performance metrics such as metrics about a creative, campaign, or account are near real-time. Metrics based on any member professional demographics such as company size and job function can be delayed by 12 to 24 hours.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#accuracy)

### Accuracy

To protect LinkedIn member privacy, professional demographic metrics are approximate. To learn more about this approximation, refer to this [article](https://www.linkedin.com/help/lms/answer/61000).

Because metrics are approximate, you can observe minor inconsistencies when comparing:

- Similar time ranges. Example: Reporting on results over 7 days vs 8 days.
- The sum of daily metrics to the full corresponding time period.
- Reporting levels. Example: Adding campaign level data and comparing it to account level data.

To minimize the effect of this approximation, select:

- A full time period instead of adding up daily metrics for that time period.
- The highest reporting level you want to view. Example: selecting account level data instead of adding up campaign level data.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#non-targeted-companies)

#### Non-Targeted Companies

Analytics can be pivoted by company name to organize results by company name and understand which companies saw a campaign or ad creative. These results can include companies that were not targeted in a campaign even if the advertiser explicitly targeted specific companies to see their campaign. This is possible for any of the following reasons:

- LinkedIn members who work at more than one company.
- LinkedIn members who switch jobs during the campaign's duration.
- Audience expansion is turned on.
- Targeted companies are parent companies of other companies.
- Advertiser changed the companies targeted during the campaign.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#metrics-available)

## Metrics Available

For more details on the schema information, refer to the [Metrics Available](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#metrics-available) table.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#professional-demographic-pivot-fields-restrictions)

#### Professional Demographic Pivot Fields Restrictions

The following fields are present only for non-demographic pivots (i.e. not MEMBER_):

- conversionValueInLocalCurrency
- cardImpressions
- cardClicks
- viralCardImpressions
- viralCardClicks
- approximateMemberReach

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#analytics-finder)

## Analytics Finder

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/jtuxa8c/ad-analytics)

The Analytics Finder is used to specify a single pivot.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_1_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_1_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=analytics&pivot={pivot}&timeGranularity={time}&dateRange={dateRange}&{facet}=List({URN_1},{URN_2})
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#query-parameters)

#### Query Parameters

For more details on the query parameters information, refer to the [Query Parameters](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#analytics-finder-query-parameters) table.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-request)

#### Sample Request

The following sample request returns creative level analytics for a particular campaign beginning in 2024.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_2_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_2_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=analytics&pivot=CREATIVE&timeGranularity=ALL&dateRange=(start:(year:2024,month:1,day:1))&campaigns=List(urn%3Ali%3AsponsoredCampaign%3A1234567)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-response)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "clicks": 177,
            "impressions": 54494,
            "dateRange": {
                "end": {
                    "day": 24,
                    "month": 5,
                    "year": 2025
                },
                "start": {
                    "day": 1,
                    "month": 1,
                    "year": 2024
                }
            },
            "pivotValues": [
                "urn:li:sponsoredCreative:1234567"
            ]
        }
    ],
    "paging": {
        "count": 10,
        "links": [],
        "start": 0
    }
}
```

 Note

- We currently don't support queries to get analytics for deleted shares that were promoted as Sponsored Content. As creatives for Sponsored Content reference a particular share, you can retrieve analytics for the deleted share by requesting analytics for the creatives that sponsored the deleted share.
- To retrieve analytics data on a video entity, you can refer to the [Video Analytics API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/video-analytics-api?view=li-lms-2026-02).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#requesting-specific-metrics-in-the-analytics-finder)

### Requesting specific metrics in the Analytics Finder

LinkedIn requires you to mention specific metrics in a request, using the `fields` query parameter. Otherwise, only `impressions` and `clicks` are returned by default. Request up to 20 metrics. The following metrics are supported:

- externalWebsiteConversions
- dateRange
- impressions
- landingPageClicks
- likes
- shares
- costInLocalCurrency
- pivotValues

 Note

Each metric is separated by a comma after the `fields=` keyword.

In the following sample request, the `fields` parameter specifies a limited set of metrics.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-request-1)

#### Sample Request

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_3_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_3_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=analytics&dateRange=(start:(year:2024,month:5,day:28),end:(year:2024,month:9,day:30))&timeGranularity=DAILY&accounts=List(urn%3Ali%3AsponsoredAccount%3A502840441)&pivot=MEMBER_COMPANY&fields=externalWebsiteConversions,dateRange,impressions,landingPageClicks,likes,shares,costInLocalCurrency,pivotValues
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-response-1)

#### Sample Response

JSON

```
{ "elements": [
        {
            "pivotValues": [
                   "urn:li:organization:1111"
             ] ,
            "dateRange": {
                "start": {
                    "month": 5,
                    "year": 2024,
                    "day": 28
                },
                "end": {
                    "month": 5,
                    "year": 2024,
                    "day": 28
                }
            },
            "landingPageClicks": 0,
            "costInLocalCurrency": "0.0",
            "impressions": 6,
            "shares": 0,
            "externalWebsiteConversions": 0,
            "likes": 0
        },
        {
             "pivotValues": [
                   "urn:li:organization:1111"
             ] ,
            "dateRange": {
                "start": {
                    "month": 5,
                    "year": 2024,
                    "day": 29
                },
                "end": {
                    "month": 5,
                    "year": 2024,
                    "day": 29
                }
            },
            "landingPageClicks": 11,
            "costInLocalCurrency": "19.91833",
            "impressions": 165,
            "shares": 0,
            "externalWebsiteConversions": 0,
            "likes": 0
        }]}

```

---

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#data-throttling)

#### Data Throttling

LinkedIn limits the amount of data that can be requested from this endpoint within a short time window. If an application exceeds the upper limit of data returned in a 5-minute window, requests are throttled. To reduce data load, use field parameters as described in the [Requesting Specific Fields in the Analytics Finder](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#requesting-specific-metrics-in-the-analytics-finder).

**Data limit for all queries over a 5 min interval: 45 million metric values** (where metric value is the value for a metric specified in the fields parameter).

Example of data limit computation for the request/response:

- Metrics requested: 9
- Number of records returned: 2 (1 per day)
- Total data cost of query: 9 *2 = 18 metric values

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#statistics-finder)

## Statistics Finder

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/rfnqk06/standard-metrics)

The `Statistics Finder` can be used to specify up to three pivots.

LinkedIn requires you to specify metrics in your request using the `fields` query parameter. Otherwise, only `impressions` and `clicks` are returned by default. You can request up to 20 metrics. For an example of a request that calls specific metrics, refer to [Requesting Specific Fields in the Analytics Finder](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#requesting-specific-metrics-in-the-analytics-finder).

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_4_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_4_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=statistics&pivots=List({pivot_1},{pivot_2},{pivot_3})&timeGranularity={time}&{facet}=List({URN_1},{URN_2})
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#query-parameters-1)

#### Query Parameters

For more details on the query parameters information, refer to the [Query Parameters](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#statistics-finder-query-parameters) table.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-request-2)

#### Sample Request

The following sample request returns campaign level statistics for a particular ad account beginning in 2024.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_5_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_5_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=statistics&pivots=List(CAMPAIGN)&dateRange=(start:(year:2024,month:1,day:1))&timeGranularity=DAILY&campaigns=List(urn:li:sponsoredAccount:1234567)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-response-2)

#### Sample Response

JSON

```
{
    "elements": [
        {
            "clicks": 177,
            "impressions": 54494,
            "dateRange": {
                "end": {
                    "day": 23,
                    "month": 5,
                    "year": 2025
                },
                "start": {
                    "day": 1,
                    "month": 1,
                    "year": 2024
                }
            },
            "pivotValues": [
                "urn:li:sponsoredCampaign:1234567"
            ]
        }
    ],
    "paging": {
        "count": 10,
        "links": [],
        "start": 0
    }
}
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#attributed-revenue-metrics-finder)

## Attributed Revenue Metrics Finder

[![Try in Postman](https://learn.microsoft.com/en-us/linkedin/media/postman-button.png?view=li-lms-2026-02)](https://www.postman.com/linkedin-developer-apis/linkedin-marketing-solutions-versioned-apis/folder/h3xcg0e/revenue-attribution)

The Attributed Revenue Metrics Finder can be used when specifying up to three pivots to demonstrate LinkedIn marketing’s influence on revenue using your CRM data. For more information, refer to the [Revenue Attribution Report](https://business.linkedin.com/marketing-solutions/revenue-attribution-report).

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#prerequisites)

### Prerequisites

To share your CRM data to Campaign Manager:

- [Set up a Business Manager for your business](https://www.linkedin.com/help/lms/answer/a726001)
- [Claim ad accounts from Campaign Manager that your business owns](https://www.linkedin.com/help/lms/answer/a416878)
- Connect one of the supported CRM to your Business Manager:
    - [Connect Salesforce CRM to Business Manager](https://www.linkedin.com/help/lms/answer/a7480664)
    - [Connect Dynamics 365 CRM to Business Manager](https://www.linkedin.com/help/lms/answer/a7484626)
    - [Connect HubSpot CRM to Business Manager](https://www.linkedin.com/help/lms/answer/a7479660)
    - [Request access to a CRM connected to your Sales Navigator in Business Manager](https://www.linkedin.com/help/lms/answer/a1678778)

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#considerations)

### Considerations

- The [RevenueAttributionMetrics](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting-schema?view=li-lms-2026-02#revenue-attribution-metrics) are only available for accounts that have connected their CRM to LinkedIn.
- After you’ve connected your CRM data to Campaign Manager, it can take up to 72 hours initially for data to be available in the response.
- Only ACCOUNT, CAMPAIGN_GROUP, CAMPAIGN pivots are supported.
- Metrics are only available within the last 1 year date range, so the dateRange must be between 30 and 366 days (inclusive).
- `opportunityAmountInUsd` and `openOpportunities` are available only when `dateRange.end` is set to today's date in UTC. Otherwise, these two fields are not returned.
- You can collate Revenue Attribution Metrics with other ad metrics (like impressions, clicks) by matching with same `pivots` and `dateRange` in other finders.

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#requesting-specific-metrics-in-the-attributed-revenue-metrics-finder)

### Requesting specific metrics in the Attributed Revenue Metrics Finder

Use `fields=revenueAttributionMetrics` to retrieve all metrics in the `RevenueAttributionMetrics` object. Alternatively, specify individual metrics by including them in the `fields` parameter, such as `fields=dateRange,pivotValues,revenueAttributionMetrics:(openOpportunities,revenueWonInUsd)`. Refer to [Field Projections](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/projections?view=li-lms-2026-02) for more details on using field projections.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_6_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_6_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=attributedRevenueMetrics&pivots=List({pivot_1},{pivot_2},{pivot_3})&account={URN_1}&{facet}=List({URN_2},{URN_3})
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#query-parameters-2)

### Query Parameters

|Parameter|Description|Format|Required|
|---|---|---|---|
|q|Designates the query finder. This must be set to `attributedRevenueMetrics` for the Attributed Revenue Metrics Finder.|String|Yes|
|pivots|Pivot of results, by which each report data point is grouped. Accepts up to 3 values. The following enum values are supported:<br><br>- CAMPAIGN - Group results by campaign.<br>- CAMPAIGN_GROUP - Group results by campaign group.<br>- ACCOUNT - Group results by account.|Array of Strings|Yes|
|dateRange.start|Represents the inclusive start time range of the analytics. Start date should be within the last 1 year.|[Date object](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext#date)|Yes|
|dateRange.end|Represents the inclusive end time range of the analytics. The field must be after start time if it's present. If unset, it indicates an open range from start time to everything after.|[Date object](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/object-types?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext#date)|No|
|account|Match result by sponsored ad account facet.|[Account URN](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/adaccounts?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext)|Yes|
|campaigns|Match result by campaign facets. Defaults to empty.|[Array of Sponsored Campaign URN](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/adcampaigngroups?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext)|No|
|campaignGroups|Match result by campaign group facets. the default value is set to empty.|[Array of Campaign Group URN](https://learn.microsoft.com/en-us/linkedin/shared/references/v2/ads/adcampaigngroups?view=li-lms-2026-02&context=linkedin%2Fmarketing%2Fcontext)|No|

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-request-3)

#### Sample Request

The following sample groups Revenue Attribution Metrics by Campaign for a particular ad account for the year 2025.

- [http](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_7_http)
- [curl](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#tabpanel_7_curl)

HTTP

```
GET https://api.linkedin.com/rest/adAnalytics?q=attributedRevenueMetrics&fields=revenueAttributionMetrics,dateRange,pivotValues&dateRange=(start:(year:2025,month:03,day:1),end:(year:2025,month:05,day:31))&account=List(urn%3Ali%3AsponsoredAccount%3A12345)&pivots=List(ACCOUNT)
```

[](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting?view=li-lms-2026-02&tabs=http#sample-response-3)

#### Sample Response

JSON

```
{
    "elements": [
        {
          "revenueAttributionMetrics": {
                "returnOnAdSpend": 10.0,
                "openOpportunities": 200,
                "opportunityWinRate": 0.75,
                "revenueWonInUsd": "1000.0",
                "closedWonOpportunities": 100,
                "opportunityAmountInUsd": "2000.0",
                "averageDaysToClose": 75.0,
                "averageDealSizeInUsd": "10.0"
          },
          "dateRange": {
                "end": {
                    "day": 31,
                    "month": 12,
                    "year": 2025
                },
                "start": {
                    "day": 1,
                    "month": 1,
                    "year": 2025
                }
            },
            "pivotValues": [
                "urn:li:sponsoredCampaign:1234567"
            ]
        }
    ],
    "paging": {
        "count": 10,
        "links": [],
        "start": 0
    }
}
```
