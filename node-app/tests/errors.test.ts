import { describe, it, expect } from "vitest";
import {
  LinkedInActionCenterError,
  AuthenticationError,
  TokenExpiredError,
  LinkedInAPIError,
  RateLimitError,
  ValidationError,
  ConfigurationError,
  StorageError,
  DataFetchError,
  handleError,
} from "../src/errors.js";

describe("Error Classes", () => {
  it("LinkedInActionCenterError stores message and details", () => {
    const err = new LinkedInActionCenterError("test error", { key: "val" });
    expect(err.message).toBe("test error");
    expect(err.details).toEqual({ key: "val" });
    expect(err.name).toBe("LinkedInActionCenterError");
  });

  it("AuthenticationError defaults message", () => {
    const err = new AuthenticationError();
    expect(err.message).toBe("Authentication failed");
  });

  it("TokenExpiredError extends AuthenticationError", () => {
    const err = new TokenExpiredError("expired", { expires_at: 123 });
    expect(err).toBeInstanceOf(AuthenticationError);
    expect(err).toBeInstanceOf(LinkedInActionCenterError);
    expect(err.details).toEqual({ expires_at: 123 });
  });

  it("LinkedInAPIError stores status code and endpoint", () => {
    const err = new LinkedInAPIError("fail", 404, { msg: "not found" }, "/test");
    expect(err.statusCode).toBe(404);
    expect(err.endpoint).toBe("/test");
    expect(err.responseData).toEqual({ msg: "not found" });
    expect(err.details.status_code).toBe(404);
  });

  it("RateLimitError sets 429 status and retry_after", () => {
    const err = new RateLimitError("rate limited", 60, "/api");
    expect(err.statusCode).toBe(429);
    expect(err.retryAfter).toBe(60);
    expect(err.details.retry_after_seconds).toBe(60);
  });

  it("ValidationError stores field and value", () => {
    const err = new ValidationError("invalid", "email", "bad@");
    expect(err.field).toBe("email");
    expect(err.value).toBe("bad@");
  });

  it("ConfigurationError stores config key", () => {
    const err = new ConfigurationError("missing", "API_KEY", "string");
    expect(err.configKey).toBe("API_KEY");
    expect(err.details.expected_type).toBe("string");
  });

  it("StorageError stores operation and table", () => {
    const err = new StorageError("failed", "insert", "campaigns");
    expect(err.operation).toBe("insert");
    expect(err.table).toBe("campaigns");
  });

  it("DataFetchError stores resource info", () => {
    const err = new DataFetchError("failed", "campaign", "123");
    expect(err.resourceType).toBe("campaign");
    expect(err.resourceId).toBe("123");
  });

  it("handleError handles custom errors without throwing", () => {
    const err = new AuthenticationError("test");
    expect(() => handleError(err)).not.toThrow();
  });

  it("handleError handles generic errors", () => {
    expect(() => handleError(new Error("generic"))).not.toThrow();
  });

  it("handleError handles non-Error values", () => {
    expect(() => handleError("string error")).not.toThrow();
  });
});
