import type { CSSProperties } from "react";
import {
  Body,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Section,
  Text,
} from "@react-email/components";

const primaryBlue = "#007BFF";
const primaryBlueLight = "#42A5F5";
const primaryBlueDark = "#1565C0";
const textColor = "#111827";
const textColorMuted = "#6B7280";
const backgroundColor = "#FFFFFF";
const borderColor = "#E5E7EB";
const fontStack = "'TASA Orbiter', 'Inter', 'Helvetica Neue', Arial, sans-serif";

export type InviteTemplateData = {
  previewText: string;
  inviteeName: string;
  orgName: string;
  invitedByName: string;
  acceptUrl: string;
  expiresText: string;
};

const defaultTemplateData: InviteTemplateData = {
  previewText: "{{PREVIEW_TEXT}}",
  inviteeName: "{{INVITEE_NAME}}",
  orgName: "{{ORG_NAME}}",
  invitedByName: "{{INVITED_BY_NAME}}",
  acceptUrl: "{{ACCEPT_URL}}",
  expiresText: "{{EXPIRES_TEXT}}",
};

export default function InviteEmail(props: Partial<InviteTemplateData>) {
  const data: InviteTemplateData = { ...defaultTemplateData, ...props };

  return (
    <Html>
      <Head>
        <style>
          {`
            @import url('https://fonts.googleapis.com/css2?family=TASA+Orbiter:wght@400;500;600;700&display=swap');
            @media screen and (max-width: 600px) {
              .container {
                width: 100% !important;
                padding: 20px !important;
                border-radius: 0 !important;
              }
              .content-wrapper {
                padding: 32px 24px !important;
              }
              .header-logo {
                width: 48px !important;
                height: auto !important;
              }
              .main-heading {
                font-size: 28px !important;
                line-height: 32px !important;
              }
              .subheading {
                font-size: 16px !important;
                line-height: 24px !important;
              }
              .invitation-card {
                padding: 28px 20px !important;
                border-radius: 16px !important;
              }
              .cta-section {
                padding: 0 !important;
                margin: 0 0 24px 0 !important;
                width: 100% !important;
                max-width: 100% !important;
              }
              .cta-section td {
                padding: 0 !important;
                width: 100% !important;
              }
              .cta-button {
                width: 100% !important;
                max-width: 100% !important;
                padding: 16px 20px !important;
                display: block !important;
                box-sizing: border-box !important;
                text-align: center !important;
              }
            }
          `}
        </style>
      </Head>
      <Preview>{data.previewText}</Preview>
      <Body style={body}>
        <Container style={container} className="container">
          {/* Header with Logo */}
          <Section style={headerSection}>
            <Img
              src="https://capmatch.com/CapMatchLogo.png"
              alt="CapMatch"
              width="56"
              height="56"
              style={logo}
              className="header-logo"
            />
          </Section>

          {/* Main Content */}
          <Section style={contentWrapper} className="content-wrapper">
            {/* Greeting */}
            <Text style={greeting}>Hello {data.inviteeName},</Text>

            {/* Main Heading */}
            <Heading style={mainHeading} className="main-heading">
              You&apos;re Invited
            </Heading>

            {/* Subheading */}
            <Text style={subheading} className="subheading">
              Join your team on CapMatch
            </Text>

            {/* Invitation Card */}
            <Section style={invitationCard} className="invitation-card">
              <Text style={cardText}>
                <strong>{data.invitedByName}</strong> has invited you to join{" "}
                <strong style={orgNameStyle}>{data.orgName}</strong> on CapMatch.
              </Text>
              <Text style={cardTextSecondary}>
                CapMatch is the platform for connecting borrowers and lenders in commercial real estate.
              </Text>
            </Section>

            {/* CTA Button */}
            <Section style={ctaSection} className="cta-section">
              <Link href={data.acceptUrl} style={ctaButton} className="cta-button">
                Accept Invitation
              </Link>
            </Section>

            {/* Expiry Notice */}
            <Text style={expiryText}>
              This invitation expires on <strong>{data.expiresText}</strong>.
            </Text>

            <Hr style={divider} />

            {/* Footer */}
            <Text style={footerText}>
              If you weren&apos;t expecting this invitation, you can safely ignore this email.
            </Text>
          </Section>
        </Container>
      </Body>
    </Html>
  );
}

const body: CSSProperties = {
  backgroundColor: "#F9FAFB",
  padding: "0",
  fontFamily: fontStack,
  color: textColor,
  margin: "0",
};

const container: CSSProperties = {
  width: "100%",
  maxWidth: "600px",
  margin: "40px auto",
  backgroundColor: backgroundColor,
  borderRadius: "12px",
  overflow: "hidden",
  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
};

const headerSection: CSSProperties = {
  textAlign: "center",
  padding: "32px 32px 0 32px",
  backgroundColor: backgroundColor,
};

const logo: CSSProperties = {
  margin: "0 auto",
  display: "block",
};

const contentWrapper: CSSProperties = {
  padding: "0 48px 48px 48px",
  backgroundColor: backgroundColor,
};

const greeting: CSSProperties = {
  fontSize: "16px",
  lineHeight: "24px",
  color: textColor,
  margin: "0 0 24px 0",
  fontWeight: 400,
};

const mainHeading: CSSProperties = {
  fontSize: "36px",
  lineHeight: "40px",
  color: textColor,
  margin: "0 0 12px 0",
  fontWeight: 700,
  textAlign: "center",
  letterSpacing: "-0.02em",
};

const subheading: CSSProperties = {
  fontSize: "18px",
  lineHeight: "28px",
  color: textColorMuted,
  margin: "0 0 32px 0",
  textAlign: "center",
  fontWeight: 400,
};

const invitationCard: CSSProperties = {
  backgroundColor: "#F8FAFF",
  borderRadius: "12px",
  padding: "32px",
  margin: "0 0 32px 0",
  border: `1px solid ${borderColor}`,
  textAlign: "center",
};

const cardText: CSSProperties = {
  fontSize: "17px",
  lineHeight: "26px",
  color: textColor,
  margin: "0 0 16px 0",
  fontWeight: 400,
};

const orgNameStyle: CSSProperties = {
  color: primaryBlue,
  fontWeight: 600,
};

const cardTextSecondary: CSSProperties = {
  fontSize: "15px",
  lineHeight: "22px",
  color: textColorMuted,
  margin: "0",
  fontWeight: 400,
};

const ctaSection: CSSProperties = {
  textAlign: "center",
  margin: "0 0 24px 0",
  width: "100%",
  maxWidth: "100%",
};

const ctaButton: CSSProperties = {
  backgroundColor: primaryBlue,
  color: "#FFFFFF",
  padding: "14px 32px",
  borderRadius: "8px",
  fontWeight: 600,
  textDecoration: "none",
  display: "inline-block",
  fontSize: "16px",
  lineHeight: "24px",
  transition: "background-color 0.2s ease",
  boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
  boxSizing: "border-box",
  maxWidth: "100%",
};

const expiryText: CSSProperties = {
  fontSize: "14px",
  lineHeight: "20px",
  color: textColorMuted,
  margin: "0 0 24px 0",
  textAlign: "center",
  fontWeight: 400,
};

const divider: CSSProperties = {
  borderColor: borderColor,
  margin: "32px 0 24px 0",
  borderWidth: "1px",
};

const footerText: CSSProperties = {
  fontSize: "13px",
  lineHeight: "20px",
  color: textColorMuted,
  margin: "0",
  textAlign: "center",
  fontWeight: 400,
};
