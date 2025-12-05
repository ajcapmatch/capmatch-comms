import { mkdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { render } from "@react-email/render";
import DigestEmail, { DigestTemplateData } from "./DigestEmail.js";
import InviteEmail, { InviteTemplateData } from "./InviteEmail.js";

const cardBaseStyle =
  "background:#F8FAFF;border-radius:20px;border:1px solid #BFDBFE;padding:24px;margin-bottom:16px;";
const projectTitleStyle = "font-size:18px;color:#3B82F6;margin:0 0 12px 0;font-weight:600;";
const statStyle =
  "display:flex;align-items:center;gap:10px;font-size:15px;color:#1F2937;margin:6px 0;font-weight:500;";

const iconStyle = "font-size:18px;line-height:1;";
const iconMessage = `<span aria-hidden="true" style="${iconStyle}">✉️</span>`;
const iconDocument = `<span aria-hidden="true" style="${iconStyle}">📄</span>`;

const sampleProjectSections = `
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Downtown Highrise Acquisition</p>
    <p style="${statStyle}">${iconMessage}<span><strong>2</strong> new messages (1 mentioned you)</span></p>
    <p style="${statStyle}">${iconDocument}<span><strong>1</strong> new document uploaded</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Seaside Retail Portfolio</p>
    <p style="${statStyle}">${iconMessage}<span><strong>1</strong> new message</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Mesa Industrial Expansion</p>
    <p style="${statStyle}">${iconDocument}<span><strong>2</strong> closing checklists updated</span></p>
  </div>
`;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
const useSampleData = process.env.USE_SAMPLE_DATA === "true";

const distDir = join(__dirname, "dist");
mkdirSync(distDir, { recursive: true });

// Render Digest Email
const sampleDigestData: DigestTemplateData = {
  previewText: "3 updates across Downtown Highrise",
  userName: "Cody Field",
  digestDateLabel: "November 27, 2025",
  ctaUrl: "https://capmatch.com/dashboard",
  managePrefsUrl: "https://capmatch.com/settings/notifications",
  projectSectionsHtml: sampleProjectSections,
};

const digestHtml = await render(
  <DigestEmail {...(useSampleData ? sampleDigestData : {})} />,
  {
    pretty: true,
  }
);

const digestOutputPath = join(distDir, "digest-template.html");
writeFileSync(digestOutputPath, digestHtml, { encoding: "utf-8" });
console.log(`Digest template rendered to ${digestOutputPath}`);

// Render Invite Email
const sampleInviteData: InviteTemplateData = {
  previewText: "You've been invited to join Acme Capital on CapMatch",
  inviteeName: "Alex Johnson",
  orgName: "Acme Capital",
  invitedByName: "Sarah Chen",
  acceptUrl: "https://capmatch.com/accept-invite?token=abc123",
  expiresText: "December 15, 2025",
};

const inviteHtml = await render(
  <InviteEmail {...(useSampleData ? sampleInviteData : {})} />,
  {
    pretty: true,
  }
);

const inviteOutputPath = join(distDir, "invite-template.html");
writeFileSync(inviteOutputPath, inviteHtml, { encoding: "utf-8" });
console.log(`Invite template rendered to ${inviteOutputPath}`);
}

main().catch((err) => {
  console.error("Failed to render email templates:", err);
  process.exit(1);
});

