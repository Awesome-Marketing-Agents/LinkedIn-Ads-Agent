/**
 * Custom exception classes for LinkedIn Action Center.
 *
 * Domain-specific errors with structured details for better
 * error handling and debugging throughout the application.
 */

export class LinkedInActionCenterError extends Error {
  details: Record<string, unknown>;

  constructor(message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;
  }

  display(): void {
    console.error(`[${this.name}] ${this.message}`);
    if (Object.keys(this.details).length > 0) {
      console.error("Details:", JSON.stringify(this.details, null, 2));
    }
  }
}

export class AuthenticationError extends LinkedInActionCenterError {
  constructor(
    message = "Authentication failed",
    details: Record<string, unknown> = {},
  ) {
    super(message, details);
  }
}

export class TokenExpiredError extends AuthenticationError {
  constructor(
    message = "Access token has expired",
    tokenInfo: Record<string, unknown> = {},
  ) {
    super(message, tokenInfo);
  }
}

export class LinkedInAPIError extends LinkedInActionCenterError {
  statusCode: number | null;
  responseData: Record<string, unknown> | null;
  endpoint: string | null;

  constructor(
    message: string,
    statusCode: number | null = null,
    responseData: Record<string, unknown> | null = null,
    endpoint: string | null = null,
  ) {
    const details: Record<string, unknown> = {};
    if (statusCode !== null) details.status_code = statusCode;
    if (endpoint) details.endpoint = endpoint;
    if (responseData) details.response = responseData;

    super(message, details);
    this.statusCode = statusCode;
    this.responseData = responseData;
    this.endpoint = endpoint;
  }
}

export class RateLimitError extends LinkedInAPIError {
  retryAfter: number | null;

  constructor(
    message = "API rate limit exceeded",
    retryAfter: number | null = null,
    endpoint: string | null = null,
  ) {
    super(message, 429, {}, endpoint);
    this.retryAfter = retryAfter;
    if (retryAfter !== null) {
      this.details.retry_after_seconds = retryAfter;
    }
  }
}

export class ValidationError extends LinkedInActionCenterError {
  field: string | null;
  value: unknown;

  constructor(
    message: string,
    field: string | null = null,
    value: unknown = null,
  ) {
    const details: Record<string, unknown> = {};
    if (field) details.field = field;
    if (value !== null) details.invalid_value = value;

    super(message, details);
    this.field = field;
    this.value = value;
  }
}

export class ConfigurationError extends LinkedInActionCenterError {
  configKey: string | null;

  constructor(
    message: string,
    configKey: string | null = null,
    expectedType: string | null = null,
  ) {
    const details: Record<string, unknown> = {};
    if (configKey) details.config_key = configKey;
    if (expectedType) details.expected_type = expectedType;

    super(message, details);
    this.configKey = configKey;
  }
}

export class StorageError extends LinkedInActionCenterError {
  operation: string | null;
  table: string | null;

  constructor(
    message: string,
    operation: string | null = null,
    table: string | null = null,
  ) {
    const details: Record<string, unknown> = {};
    if (operation) details.operation = operation;
    if (table) details.table = table;

    super(message, details);
    this.operation = operation;
    this.table = table;
  }
}

export class DataFetchError extends LinkedInActionCenterError {
  resourceType: string | null;
  resourceId: string | null;

  constructor(
    message: string,
    resourceType: string | null = null,
    resourceId: string | null = null,
  ) {
    const details: Record<string, unknown> = {};
    if (resourceType) details.resource_type = resourceType;
    if (resourceId) details.resource_id = resourceId;

    super(message, details);
    this.resourceType = resourceType;
    this.resourceId = resourceId;
  }
}

export function handleError(
  error: unknown,
  showTraceback = false,
): void {
  if (error instanceof LinkedInActionCenterError) {
    error.display();
  } else if (error instanceof Error) {
    console.error(`[${error.name}] ${error.message}`);
  } else {
    console.error("[UnknownError]", error);
  }

  if (showTraceback && error instanceof Error && error.stack) {
    console.error(error.stack);
  }
}
