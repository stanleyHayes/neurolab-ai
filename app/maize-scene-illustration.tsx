export function FallbackIllustration() {
  return (
    <svg
      className="maize-fallback-art"
      viewBox="0 0 320 330"
      role="img"
      aria-label="Illustrative maize plant, leaf and root structure"
    >
      <defs>
        <linearGradient id="fallback-leaf" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#28784a" />
          <stop offset="1" stopColor="#90c875" />
        </linearGradient>
      </defs>
      <path
        d="M160 243 C155 195 159 139 162 68"
        fill="none"
        stroke="#a7bd67"
        strokeWidth="11"
        strokeLinecap="round"
      />
      <path
        d="M158 191 C104 196 65 168 38 124 C83 123 129 145 160 173Z"
        fill="url(#fallback-leaf)"
        stroke="#b8d68d"
      />
      <path
        d="M160 158 C212 160 253 128 276 87 C230 91 188 111 161 139Z"
        fill="url(#fallback-leaf)"
        stroke="#b8d68d"
      />
      <path
        d="M161 120 C121 119 91 96 74 59 C112 65 142 83 163 106Z"
        fill="url(#fallback-leaf)"
        stroke="#b8d68d"
      />
      <path
        d="M164 95 C200 89 223 66 235 34 C207 41 184 57 166 78Z"
        fill="url(#fallback-leaf)"
        stroke="#b8d68d"
      />
      <path
        d="M160 240 C137 264 137 278 115 299 M160 240 C180 270 184 282 205 301 M160 241 C154 267 158 286 156 308 M161 243 C193 249 213 261 233 276 M158 247 C125 255 98 267 82 280"
        fill="none"
        stroke="#c69b66"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M160 192 45 129 M161 159 273 91 M163 119 77 63 M164 94 233 39"
        fill="none"
        stroke="#d0dfa2"
        strokeWidth="1.5"
      />
    </svg>
  );
}
