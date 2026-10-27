import type { ReactNode } from "react";

type AuthFieldProps = {
  label: string;
  name: string;
  type: string;
  autocomplete: string;
  placeholder: string;
  icon: ReactNode;
  registering: boolean;
  minLength?: number;
  maxLength?: number;
  suffix?: ReactNode;
};

function FieldIcon({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <span className="auth-field-icon" aria-hidden="true">
      {children}
    </span>
  );
}

export function AuthField({
  label,
  name,
  type,
  autocomplete,
  placeholder,
  icon,
  registering,
  minLength,
  maxLength,
  suffix,
}: Readonly<AuthFieldProps>) {
  return (
    <label className="auth-field">
      <span id={`auth-${name}-label`}>{label}</span>
      <span className="auth-input-wrap">
        <FieldIcon>{icon}</FieldIcon>
        <input
          name={name}
          aria-labelledby={`auth-${name}-label`}
          type={type}
          autoComplete={autocomplete}
          required
          minLength={minLength}
          maxLength={maxLength}
          placeholder={placeholder}
        />
        {suffix}
      </span>
      {name === "password" && registering && (
        <small>Use at least 12 characters.</small>
      )}
    </label>
  );
}
