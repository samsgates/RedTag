variable "project_id" { type = string }
variable "region" { type = string default = "us-central1" }
variable "environment" { type = string default = "prod" }
variable "api_image" { type = string }
variable "web_image" { type = string }
variable "database_tier" { type = string default = "db-custom-2-7680" }
variable "database_name" { type = string default = "redtag" }
variable "database_user" { type = string default = "redtag" }
variable "allow_public_web" { type = bool default = true }
variable "allow_public_api" { type = bool default = true }
variable "jwt_issuer" { type = string description = "OIDC token issuer, for Firebase use https://securetoken.google.com/PROJECT_ID" }
variable "jwt_audience" { type = string description = "OIDC audience, for Firebase use the Firebase project ID" }
variable "jwks_url" { type = string description = "JWKS endpoint used to validate user bearer tokens" }
variable "web_origin" { type = string default = "http://localhost:3000" description = "Allowed browser origin. Replace with the production web origin." }
variable "default_tenant_id" { type = string default = "tenant_demo" }

variable "model_armor_location" { type = string default = "us-central1" }
variable "model_armor_template" { type = string default = "" description = "Existing Model Armor template ID. Empty disables cloud screening." }
