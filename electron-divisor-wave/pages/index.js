import { useState, useEffect, useCallback, useRef } from 'react'
import katex from 'katex'

// ── Data ────────────────────────────────────────────────────────────────────
const FUNCTIONS = [
  { id: '1',  name: 'Product of Sin',                  group: 'Basic' },
  { id: '2',  name: 'Product Rep. for Sin',             group: 'Basic' },
  { id: '3',  name: 'Product Rep. for Sin (Complex)',   group: 'Basic', broken: true },
  { id: '4',  name: 'Complex Playground Demo',          group: 'Basic' },
  { id: '5',  name: 'Riesz — Cos',                     group: 'Riesz' },
  { id: '6',  name: 'Riesz — Sin',                     group: 'Riesz' },
  { id: '7',  name: 'Riesz — Tan',                     group: 'Riesz' },
  { id: '8',  name: 'Viète — Cos',                     group: 'Viète' },
  { id: '9',  name: 'Viète — Sin',                     group: 'Viète' },
  { id: '10', name: 'Viète — Tan',                     group: 'Viète' },
  { id: '11', name: 'Cos of Product of Sin',            group: 'Compositions' },
  { id: '12', name: 'Sin of Product of Sin',            group: 'Compositions' },
  { id: '13', name: 'Cos of Product Rep. of Sin',       group: 'Compositions' },
  { id: '14', name: 'Sin of Product Rep. of Sin',       group: 'Compositions' },
  { id: '15', name: 'Binary Prime Indicator H',         group: 'Prime' },
  { id: '16', name: 'Prime Output Indicator J',         group: 'Prime' },
  { id: '17', name: 'BOPIF Q Alternation Series',       group: 'Prime' },
  { id: '18', name: 'Dirichlet Eta from BOPIF',         group: 'Prime' },
  { id: '19', name: '|loggamma(z)|',                    group: 'Analytic' },
  { id: '20', name: '1 / (1 + z²)',                     group: 'Analytic' },
  { id: '21', name: '|z^z|',                            group: 'Analytic' },
  { id: '22', name: 'gamma(z)',                          group: 'Analytic' },
  { id: '23', name: 'Log of Product Rep. Sin',          group: 'Transforms' },
  { id: '24', name: 'Gamma of Product Rep. Sin',        group: 'Transforms' },
  { id: '25', name: 'Gamma Form Product Rep. Sin',      group: 'Transforms' },
  { id: '26', name: 'Custom Riesz — Tan',              group: 'Custom' },
  { id: '27', name: 'Custom Viète — Cos',              group: 'Custom' },
  { id: '28', name: 'Half-Base Viète — Sin',           group: 'Custom' },
  { id: '29', name: 'Log-Power-Base Viète — Sin',      group: 'Custom' },
  { id: '30', name: 'Riesz Tan + Prime Indicator',      group: 'Custom' },
  { id: '31', name: 'Nested Roots Product for 2',       group: 'Experimental' },
  { id: '32', name: 'Product Factory',                  group: 'Experimental', broken: true },
]

const COLORMAPS = [
  { id: '1', name: 'Prism',   stops: ['#f00','#ff0','#0f0','#00f','#f0f'] },
  { id: '2', name: 'Jet',     stops: ['#00008b','#0080ff','#00ff00','#ff8000','#8b0000'] },
  { id: '3', name: 'Plasma',  stops: ['#0d0887','#7e03a8','#cc4778','#f89540','#f0f921'] },
  { id: '4', name: 'Viridis', stops: ['#440154','#31688e','#21908c','#35b779','#fde725'] },
  { id: '5', name: 'Magma',   stops: ['#000004','#3b0f70','#8c2981','#de4968','#fde0c8'] },
]

const FN_DEFAULTS = {
  '1':  { both: { m: 0.0465,  beta: 0.178  }, note: 'tuned amplitude for product of sin'       },
  '2':  { N:    { m: 0.0125,  beta: 0.078  },
           Y:    { m: 0.36,    beta: 0.1468 }, note: 'norm needs 30× higher m to pull detail'   },
  '3':  { both: null,                          note: 'not implemented — will error'              },
  '4':  { both: { m: 0.0125,  beta: 0.054  }, note: 'Riesz cos 3 variant'                      },
  '5':  { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '6':  { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '7':  { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '8':  { N:    { m: 0.07,    beta: 1      },
           Y:    { m: 0.27,    beta: 1      }, note: 'large m needed — Viète converges fast'    },
  '9':  { N:    { m: 0.87,    beta: 1      },
           Y:    { m: 0.87,    beta: 0.4   }, note: 'very large m — sin Viète needs strong pull'},
  '10': { N:    { m: 0.007,   beta: 0.004  },
           Y:    { m: 0.004,   beta: 0.004  }, note: 'tiny m — tan Viète diverges easily'       },
  '11': { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '12': { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '13': { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '14': { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '15': { both: { m: 0.029,   beta: 0.025  }, note: 'prime fn — also uses c & α coefficients'  },
  '16': { both: { m: 0.029,   beta: 0.025  }, note: 'prime fn — also uses c & α coefficients'  },
  '17': { both: { m: 0.029,   beta: 0.025  }, note: 'prime fn — also uses c & α coefficients'  },
  '18': { both: { m: 0.029,   beta: 0.025  }, note: 'prime fn — also uses c & α coefficients'  },
  '19': { both: null,                          note: 'basic analytic — no m/β'                  },
  '20': { both: null,                          note: 'basic analytic — no m/β (OG has ^ bug)'   },
  '21': { both: null,                          note: 'basic analytic — no m/β'                  },
  '22': { both: null,                          note: 'basic analytic — no m/β'                  },
  '23': { both: { m: 0.0125,  beta: 0.078  }, note: 'inherits last m/β — set manually'         },
  '24': { both: { m: 0.0125,  beta: 0.078  }, note: 'inherits last m/β — set manually'         },
  '25': { both: { m: 0.0125,  beta: 0.054  }, note: ''                                          },
  '26': { both: { m: 0.001,   beta: 0.07   }, note: 'very small m — keep surface tame'         },
  '27': { both: { m: 0.001,   beta: 0.07   }, note: 'very small m — keep surface tame'         },
  '28': { N:    { m: 0.07,    beta: 1      },
           Y:    { m: 0.37,    beta: 0.07  }, note: ''                                           },
  '29': { both: { m: 0.001,   beta: 0.07   }, note: 'very small m — log-power grows fast'      },
  '30': { both: { m: 0.001,   beta: 0.07   }, note: 'combination fn — q=0.08 also baked in'    },
  '31': { both: { m: 0.001,   beta: 0.07   }, note: 'nested roots — paradox variant'            },
  '32': { both: null,                          note: 'product factory — broken in OG'            },
}

function getFnDefaults(functionId, normalize) {
  const entry = FN_DEFAULTS[String(functionId)]
  if (!entry) return null
  if (entry.both !== undefined) return entry.both
  return entry[normalize] ?? entry.N ?? null
}

const DEFAULT_PARAMS = {
  functionId:   '1',
  normalize:    'N',
  colNormalize: false,
  powerStretch: null,
  colormap:     '4',
  resolution:   0.1,
  xmin:  2, xmax: 20,
  ymin: -5, ymax:  5,
  elev: 30,  azim: -70,
  m:    null,
  beta: null,
  mode: '3d',
}

// ── Design tokens ──────────────────────────────────────────────────────────
const T = {
  bg:          '#06060e',
  titlebar:    'rgba(8, 7, 18, 0.97)',
  sidebar:     'rgba(10, 9, 22, 0.93)',
  glass:       'rgba(255, 255, 255, 0.028)',
  glassBright: 'rgba(255, 255, 255, 0.055)',
  border:      'rgba(255, 255, 255, 0.072)',
  borderHover: 'rgba(180, 160, 255, 0.32)',
  accent:      '#b4a0ff',
  accentSoft:  'rgba(180, 160, 255, 0.11)',
  accentGlow:  'rgba(150, 120, 255, 0.22)',
  warn:        '#fbbf24',
  text:        '#edeaf8',
  muted:       '#7874a0',
  dim:         '#38345a',
  mono:        '"SF Mono","Fira Code","Consolas",monospace',
  radius:      '12px',
  radiusSm:    '8px',
  radiusPill:  '999px',
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fmtCount(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'k'
  return String(n)
}

function Label({ children }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 700, letterSpacing: '0.16em',
      color: T.muted, textTransform: 'uppercase', marginBottom: 7,
      fontFamily: T.mono,
    }}>
      {children}
    </div>
  )
}

function Card({ children, style }) {
  return (
    <div style={{
      background: T.glass, border: `1px solid ${T.border}`,
      borderRadius: T.radius, padding: '11px 12px', ...style,
    }}>
      {children}
    </div>
  )
}

function GradBar({ stops }) {
  return (
    <div style={{
      height: 4, borderRadius: T.radiusPill, flexShrink: 0,
      background: `linear-gradient(90deg, ${stops.join(',')})`,
    }} />
  )
}

// ── Slider + inline-editable text ──────────────────────────────────────────
function ParamControl({ label, value, min, max, step, onChange, fmt, noSlider }) {
  const [draft, setDraft] = useState(null)
  const inputRef          = useRef()
  const display = draft !== null ? draft : (fmt ? fmt(value) : String(value))

  const commit = (raw) => {
    const n = parseFloat(raw)
    if (!isNaN(n)) onChange(n)
    setDraft(null)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: noSlider ? 0 : 5 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: T.muted }}>{label}</span>
        <input
          ref={inputRef}
          type="text"
          value={display}
          onFocus={e => { setDraft(String(value)); e.target.select() }}
          onChange={e => setDraft(e.target.value)}
          onBlur={e  => commit(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') { e.preventDefault(); commit(draft); inputRef.current?.blur() }
            if (e.key === 'Escape') { setDraft(null); inputRef.current?.blur() }
          }}
          style={{
            width: 60, textAlign: 'right',
            background: draft !== null ? 'rgba(180,160,255,0.09)' : 'transparent',
            border: draft !== null ? `1px solid ${T.borderHover}` : '1px solid transparent',
            color: draft !== null ? T.text : T.accent,
            fontFamily: T.mono, fontSize: 11,
            borderRadius: 6, padding: '2px 6px', outline: 'none',
            transition: 'all 0.15s', cursor: 'text',
          }}
        />
      </div>
      {!noSlider && (
        <input
          type="range" min={min} max={max} step={step}
          value={Math.min(max, Math.max(min, value))}
          onChange={e => { onChange(Number(e.target.value)); setDraft(null) }}
          style={{ width: '100%', accentColor: T.accent, cursor: 'pointer' }}
        />
      )}
    </div>
  )
}

// ── Panel / Sidebar icon (SVG) ─────────────────────────────────────────────
function PanelIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ display: 'block', flexShrink: 0 }}
    >
      <rect x="1" y="1" width="14" height="14" rx="2" />
      <line x1="5.5" y1="1" x2="5.5" y2="15" />
    </svg>
  )
}

// ── Collapsible section ────────────────────────────────────────────────────
function Section({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div style={{
      borderRadius: T.radius,
      border: `1px solid ${T.border}`,
      overflow: 'hidden',
    }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 8,
          padding: '9px 12px',
          background: open ? T.glassBright : T.glass,
          border: 'none', cursor: 'pointer',
          transition: 'background 0.15s',
        }}
      >
        <span style={{
          flex: 1, textAlign: 'left',
          fontSize: 9, fontWeight: 700, letterSpacing: '0.16em',
          textTransform: 'uppercase', color: T.muted, fontFamily: T.mono,
        }}>
          {title}
        </span>
        <span style={{
          fontSize: 10, color: T.dim,
          display: 'inline-block',
          transition: 'transform 0.2s',
          transform: open ? 'rotate(0deg)' : 'rotate(-90deg)',
        }}>▾</span>
      </button>
      <div style={{
        maxHeight: open ? '1800px' : '0',
        overflow: 'hidden',
        transition: 'max-height 0.28s cubic-bezier(0.4,0,0.2,1)',
      }}>
        <div style={{
          padding: '10px 12px',
          display: 'flex', flexDirection: 'column', gap: 10,
          background: 'rgba(0,0,0,0.18)',
          borderTop: `1px solid ${T.border}`,
        }}>
          {children}
        </div>
      </div>
    </div>
  )
}

// ── Formula panel (collapsible bar + custom function library) ──────────────
const MINT   = '#6ee7b7'   // mint green — operators / actions
const MINTBG = 'rgba(110,231,183,0.07)'

function FormulaPanel({
  functionId, formulasMap, termsMap, userFunctions,
  open, onToggleOpen,
  editMode, onEnterEdit, onExitEdit,
  onUserFnsChanged, isElectron,
}) {
  const formulaRef = useRef(null)

  // Draft state for the editor
  const [draft,      setDraft]      = useState({ id: null, name: '', latex: '', m: 0.0125, beta: 0.054 })
  const [isEditing,  setIsEditing]  = useState(false)
  const [validation, setValidation] = useState(null)
  const [validating, setValidating] = useState(false)
  const [saving,     setSaving]     = useState(false)
  // Dynamically measured height of the rendered KaTeX formula
  const [formulaH,   setFormulaH]   = useState(100)

  // Pre-load draft when editMode activates
  useEffect(() => {
    if (!editMode) { setValidation(null); return }
    const fidStr   = String(functionId)
    const isCustom = fidStr.startsWith('u')
    const uf       = (userFunctions || []).find(f => f.id === fidStr)

    if (isCustom && uf) {
      setDraft({ id: uf.id, name: uf.name, latex: uf.latex,
                 m: uf.defaults?.m ?? 0.0125, beta: uf.defaults?.beta ?? 0.054 })
      setIsEditing(true)
    } else {
      // Built-in: use term if available, else empty
      const term = (termsMap || {})[fidStr] || ''
      setDraft({ id: null, name: '', latex: term, m: 0.0125, beta: 0.054 })
      setIsEditing(false)
    }
    setValidation(null)
  }, [editMode, functionId])

  // KaTeX rendering (view mode)
  useEffect(() => {
    if (!formulaRef.current || editMode) return
    let latex = (formulasMap || {})[String(functionId)] || ''
    if (!latex) {
      const uf = (userFunctions || []).find(f => f.id === functionId)
      if (uf?.latex) latex = `\\left|\\prod_{k=2}^{\\lfloor x\\rfloor}${uf.latex}\\right|^{-m}`
    }
    if (!latex) { formulaRef.current.innerHTML = ''; return }
    try {
      formulaRef.current.innerHTML = katex.renderToString(latex, {
        throwOnError: false, displayMode: true, output: 'html', strict: false,
      })
    } catch { formulaRef.current.textContent = latex }
    // Measure the rendered height after the browser has laid it out,
    // then expand the panel to fit with comfortable vertical breathing room.
    requestAnimationFrame(() => {
      if (!formulaRef.current) return
      const h = formulaRef.current.scrollHeight
      if (h > 10) setFormulaH(h + 32) // +32px top/bottom padding
    })
  }, [functionId, formulasMap, userFunctions, editMode, open])

  async function handleValidate() {
    if (!isElectron || !draft.latex.trim()) return
    setValidating(true); setValidation(null)
    try {
      const r = await window.electronAPI.validateUserFunction(draft.latex.trim())
      setValidation({ ok: r.success, message: r.message || r.error || '' })
    } finally { setValidating(false) }
  }

  async function handleSave(asNew = false) {
    if (!isElectron || !draft.name.trim() || !draft.latex.trim()) return
    setSaving(true)
    try {
      const fn = {
        ...(!asNew && draft.id ? { id: draft.id } : {}),
        name: draft.name.trim(), latex: draft.latex.trim(),
        defaults: { m: draft.m, beta: draft.beta },
      }
      const r = await window.electronAPI.saveUserFunction(fn)
      if (r.success) {
        onUserFnsChanged?.()
        if (asNew || !draft.id) {
          setDraft({ id: null, name: '', latex: '', m: 0.0125, beta: 0.054 })
          setIsEditing(false)
        }
        setValidation(null)
      }
    } finally { setSaving(false) }
  }

  async function handleDelete(id) {
    if (!isElectron) return
    await window.electronAPI.deleteUserFunction(id)
    onUserFnsChanged?.()
    if (draft.id === id) { setDraft({ id: null, name: '', latex: '', m: 0.0125, beta: 0.054 }); setIsEditing(false) }
  }

  function loadForEdit(uf) {
    setDraft({ id: uf.id, name: uf.name, latex: uf.latex, m: uf.defaults?.m ?? 0.0125, beta: uf.defaults?.beta ?? 0.054 })
    setIsEditing(true); setValidation(null)
  }

  function loadAsCopy(uf) {
    setDraft({ id: null, name: '', latex: uf.latex, m: uf.defaults?.m ?? 0.0125, beta: uf.defaults?.beta ?? 0.054 })
    setIsEditing(false); setValidation(null)
  }

  function loadFromCurrent() {
    const fidStr = String(functionId)
    const term   = (termsMap || {})[fidStr] || ''
    setDraft(d => ({ ...d, latex: term || d.latex }))
    setValidation(null)
  }

  const canSave    = !!(draft.name.trim() && draft.latex.trim() && validation?.ok)
  const panelH     = !open ? 28 : (editMode ? 300 : 28 + formulaH)

  // Header button shared style
  const hdrBtn = (active = false) => ({
    padding: '2px 8px', borderRadius: T.radiusPill, cursor: 'pointer',
    border: `1px solid ${active ? 'rgba(110,231,183,0.35)' : T.border}`,
    background: active ? MINTBG : 'transparent',
    color: active ? MINT : T.dim,
    fontFamily: T.mono, fontSize: 9, transition: 'all 0.15s',
  })

  return (
    <div style={{
      flexShrink: 0, height: panelH,
      transition: 'height 0.25s cubic-bezier(0.4,0,0.2,1)',
      background: 'rgba(3,3,10,0.98)',
      borderTop: `1px solid ${T.border}`,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      {/* ── Header bar ── */}
      <div style={{
        height: 28, flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 7,
        padding: '0 12px',
        borderBottom: open ? `1px solid ${T.border}` : 'none',
      }}>
        <button onClick={onToggleOpen} style={{
          padding: 0, width: 18, height: 18, border: 'none',
          background: 'transparent', color: T.dim, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, transform: open ? 'rotate(0deg)' : 'rotate(-90deg)',
          transition: 'transform 0.2s', flexShrink: 0,
        }}>▾</button>

        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
          color: T.dim, fontFamily: T.mono, flex: 1 }}>
          {editMode ? 'Custom Library' : 'Formula'}
        </span>

        {editMode
          ? <button onClick={onExitEdit} style={hdrBtn()}>✕ close</button>
          : <button onClick={onEnterEdit} style={hdrBtn(true)}>⊕ custom</button>
        }
      </div>

      {/* ── View mode: rendered KaTeX ── */}
      {open && !editMode && (
        <div
          onDoubleClick={onEnterEdit}
          title="Double-click to open Custom Library"
          style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '0 56px', overflow: 'hidden', position: 'relative', cursor: 'default',
          }}
        >
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 56, zIndex: 1, pointerEvents: 'none',
            background: 'linear-gradient(90deg,rgba(3,3,10,0.98) 0%,transparent 100%)' }} />
          <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 56, zIndex: 1, pointerEvents: 'none',
            background: 'linear-gradient(270deg,rgba(3,3,10,0.98) 0%,transparent 100%)' }} />
          <div ref={formulaRef} className="formula-panel" style={{ color: T.text }} />
        </div>
      )}

      {/* ── Edit mode: custom library + editor ── */}
      {open && editMode && (
        <div style={{ flex: 1, display: 'flex', gap: 0, overflow: 'hidden', minHeight: 0 }}>

          {/* Left panel: saved custom functions */}
          <div style={{
            width: 172, flexShrink: 0, borderRight: `1px solid ${T.border}`,
            display: 'flex', flexDirection: 'column', padding: '8px 8px', gap: 4,
            overflowY: 'auto',
          }}>
            <span style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase',
              color: T.dim, fontFamily: T.mono, marginBottom: 2 }}>Saved</span>

            {/* Use current function as template */}
            <button onClick={loadFromCurrent} style={{
              padding: '5px 8px', borderRadius: T.radiusSm, cursor: 'pointer',
              border: `1px solid rgba(110,231,183,0.22)`,
              background: MINTBG, color: MINT,
              fontSize: 10, fontFamily: T.mono, textAlign: 'left',
              display: 'flex', alignItems: 'center', gap: 5,
            }}>
              <span>⊕</span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                flex: 1, fontSize: 9 }}>
                template from fn {functionId}
              </span>
            </button>

            {userFunctions.length === 0 && (
              <div style={{ fontSize: 9, color: T.dim, fontFamily: T.mono, padding: '2px 0', opacity: 0.6 }}>
                no custom functions yet
              </div>
            )}

            {userFunctions.map(uf => (
              <div key={uf.id} style={{
                display: 'flex', alignItems: 'center', gap: 3,
                padding: '5px 7px', borderRadius: T.radiusSm,
                border: `1px solid ${draft.id === uf.id ? T.borderHover : T.border}`,
                background: draft.id === uf.id ? T.accentSoft : 'rgba(0,0,0,0.2)',
              }}>
                <button onClick={() => loadForEdit(uf)} style={{
                  flex: 1, textAlign: 'left', border: 'none', background: 'transparent',
                  cursor: 'pointer', padding: 0,
                  color: draft.id === uf.id ? T.accent : T.text,
                  fontSize: 10, fontFamily: T.mono,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  <span style={{ color: T.dim, fontSize: 9 }}>{uf.id}. </span>{uf.name}
                </button>
                <button onClick={() => loadAsCopy(uf)} title="Copy as new"
                  style={{ fontSize: 9, padding: '1px 4px', flexShrink: 0,
                    border: `1px solid ${T.border}`, borderRadius: 4,
                    background: 'transparent', color: T.dim, cursor: 'pointer' }}>⧉</button>
                <button onClick={() => handleDelete(uf.id)} title="Delete"
                  style={{ fontSize: 9, padding: '1px 4px', flexShrink: 0,
                    border: '1px solid rgba(255,80,80,0.2)', borderRadius: 4,
                    background: 'transparent', color: 'rgba(255,100,100,0.65)', cursor: 'pointer' }}>×</button>
              </div>
            ))}
          </div>

          {/* Right panel: editor form */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6,
            padding: '8px 12px', overflowY: 'auto', minWidth: 0 }}>

            <span style={{ fontSize: 8, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase',
              color: isEditing ? MINT : T.dim, fontFamily: T.mono }}>
              {isEditing ? `editing ${draft.id}` : 'new function'}
            </span>

            {/* Name */}
            <input type="text" value={draft.name}
              onChange={e => setDraft(d => ({ ...d, name: e.target.value }))}
              placeholder={isEditing ? 'Function name' : 'Name for new function…'}
              style={{ width: '100%', background: 'rgba(0,0,0,0.32)',
                border: `1px solid ${T.border}`, borderRadius: T.radiusSm,
                color: T.text, padding: '5px 9px', fontSize: 11, fontFamily: T.mono, outline: 'none' }} />

            {/* LaTeX term */}
            <textarea value={draft.latex} rows={2}
              onChange={e => { setDraft(d => ({ ...d, latex: e.target.value })); setValidation(null) }}
              placeholder={`\\beta\\frac{x}{k}\\sin\\left(\\frac{\\pi z}{k}\\right)  ← term inside ∏`}
              style={{ width: '100%', background: 'rgba(0,0,0,0.32)',
                border: `1px solid ${T.border}`, borderRadius: T.radiusSm,
                color: '#b0e8cc', padding: '5px 9px', fontSize: 10,
                fontFamily: T.mono, outline: 'none', resize: 'none', lineHeight: 1.55 }} />

            {/* Coefficients row + buttons */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
              {/* m */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 9, color: T.dim, fontFamily: T.mono }}>m</span>
                <input type="number" value={draft.m} step={0.001} min={0.0001} max={2}
                  onChange={e => setDraft(d => ({ ...d, m: parseFloat(e.target.value) || 0.0125 }))}
                  style={{ width: 68, background: 'rgba(0,0,0,0.32)', border: `1px solid ${T.border}`,
                    borderRadius: T.radiusSm, color: T.text, padding: '4px 7px',
                    fontSize: 11, fontFamily: T.mono, outline: 'none' }} />
              </div>
              {/* β */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 9, color: T.dim, fontFamily: T.mono }}>β</span>
                <input type="number" value={draft.beta} step={0.001} min={0.0001} max={2}
                  onChange={e => setDraft(d => ({ ...d, beta: parseFloat(e.target.value) || 0.054 }))}
                  style={{ width: 68, background: 'rgba(0,0,0,0.32)', border: `1px solid ${T.border}`,
                    borderRadius: T.radiusSm, color: T.text, padding: '4px 7px',
                    fontSize: 11, fontFamily: T.mono, outline: 'none' }} />
              </div>

              {/* Action buttons */}
              <button onClick={handleValidate} disabled={validating || !draft.latex.trim()} style={{
                padding: '4px 10px', borderRadius: T.radiusSm, fontFamily: T.mono, fontSize: 10,
                border: `1px solid rgba(110,231,183,0.28)`, background: MINTBG, color: MINT,
                cursor: draft.latex.trim() ? 'pointer' : 'not-allowed',
                opacity: draft.latex.trim() ? 1 : 0.5,
              }}>{validating ? '…' : 'validate'}</button>

              {isEditing && (
                <button onClick={() => handleSave(false)} disabled={saving || !canSave} style={{
                  padding: '4px 10px', borderRadius: T.radiusSm, fontFamily: T.mono, fontSize: 10,
                  border: `1px solid ${canSave ? T.borderHover : T.border}`,
                  background: canSave ? T.accentSoft : 'rgba(0,0,0,0.2)',
                  color: canSave ? T.accent : T.dim, cursor: canSave ? 'pointer' : 'not-allowed',
                }}>{saving ? '…' : 'update'}</button>
              )}

              <button onClick={() => handleSave(true)} disabled={saving || !canSave} style={{
                padding: '4px 10px', borderRadius: T.radiusSm, fontFamily: T.mono, fontSize: 10,
                border: `1px solid ${canSave ? 'rgba(110,231,183,0.32)' : T.border}`,
                background: canSave ? MINTBG : 'rgba(0,0,0,0.2)',
                color: canSave ? MINT : T.dim, cursor: canSave ? 'pointer' : 'not-allowed',
                marginLeft: 'auto',
              }}>{saving ? '…' : 'save new'}</button>
            </div>

            {/* Validation result */}
            {validation && (
              <div style={{
                fontSize: 9, fontFamily: T.mono, lineHeight: 1.4, padding: '4px 8px',
                borderRadius: T.radiusSm, wordBreak: 'break-all',
                background: validation.ok ? 'rgba(99,200,120,0.07)' : 'rgba(255,80,80,0.06)',
                border: `1px solid ${validation.ok ? 'rgba(99,200,120,0.2)' : 'rgba(255,80,80,0.18)'}`,
                color: validation.ok ? 'rgba(130,230,150,0.85)' : '#ff8080',
              }}>
                {validation.ok ? '✓ ' : '✗ '}{validation.message}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Traffic light (bigger) ─────────────────────────────────────────────────
function TrafficLight({ color, hoverColor, onClick, symbol }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        width: 17, height: 17, borderRadius: '50%', border: 'none',
        background: hov ? hoverColor : color,
        cursor: 'pointer', padding: 0, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, color: 'rgba(0,0,0,0.65)', fontWeight: 900,
        WebkitAppRegion: 'no-drag',
        transition: 'background 0.12s, transform 0.1s',
        transform: hov ? 'scale(1.12)' : 'scale(1)',
      }}
    >
      {hov ? symbol : ''}
    </button>
  )
}

// ── Title bar ──────────────────────────────────────────────────────────────
function TitleBar({ sidebarOpen, onToggle, isElectron }) {
  const api = isElectron ? window.electronAPI.window : {}
  return (
    <div style={{
      height: 44, flexShrink: 0, zIndex: 200,
      background: T.titlebar,
      backdropFilter: 'blur(40px)', WebkitBackdropFilter: 'blur(40px)',
      borderBottom: `1px solid ${T.border}`,
      display: 'flex', alignItems: 'center',
      WebkitAppRegion: 'drag', userSelect: 'none',
    }}>
      {/* Sidebar toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', WebkitAppRegion: 'no-drag' }}>
        <button
          onClick={onToggle}
          style={{
            background: T.glass, border: `1px solid ${T.border}`,
            color: T.muted, cursor: 'pointer',
            width: 30, height: 30, borderRadius: T.radiusSm,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 0, transition: 'all 0.15s',
          }}
          title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <PanelIcon size={15} />
        </button>
      </div>

      {/* App title */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', WebkitAppRegion: 'drag' }}>
        <span style={{
          fontSize: 16,
          fontWeight: 800,
          fontFamily: "'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          background: 'linear-gradient(130deg, #ffffff 20%, #c4b0ff 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.01em',
          lineHeight: 1,
        }}>
          Divisor Wave
        </span>
      </div>

      {/* Window controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '0 18px', WebkitAppRegion: 'no-drag' }}>
        <TrafficLight color="#ffbd44" hoverColor="#ffca5e" onClick={() => api.minimize?.()} symbol="–" />
        <TrafficLight color="#00ca4e" hoverColor="#2ee870" onClick={() => api.maximize?.()} symbol="+" />
        <TrafficLight color="#ff605c" hoverColor="#ff7a77" onClick={() => api.close?.()}    symbol="×" />
      </div>
    </div>
  )
}

// ── Coefficients card ──────────────────────────────────────────────────────
function CoefficientsCard({ params, set, isElectron }) {
  const [autoLoading, setAutoLoading] = useState(false)
  const [autoNote,    setAutoNote]    = useState(null)

  const custom  = params.m !== null || params.beta !== null
  const fnDefs  = getFnDefaults(params.functionId, params.normalize)
  const hasDefs = fnDefs !== null
  const note    = FN_DEFAULTS[String(params.functionId)]?.note ?? ''

  function enableCustom() {
    set('m')(fnDefs?.m ?? 0.0125)
    set('beta')(fnDefs?.beta ?? 0.054)
  }

  function resetToDefaults() {
    set('m')(null)
    set('beta')(null)
    setAutoNote(null)
  }

  async function runAuto() {
    if (!isElectron || !hasDefs) return
    setAutoLoading(true)
    setAutoNote(null)
    try {
      const r = await window.electronAPI.autoCoeffs({
        functionId: params.functionId,
        normalize:  params.normalize,
        xmin: params.xmin, xmax: params.xmax,
        ymin: params.ymin, ymax: params.ymax,
      })
      if (r.success) {
        set('m')(r.m)
        set('beta')(r.beta)
        setAutoNote(r.note)
      } else {
        setAutoNote('auto failed: ' + (r.error || 'unknown'))
      }
    } finally {
      setAutoLoading(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <Label>Coefficients</Label>
        <div style={{ display: 'flex', gap: 5 }}>
          {isElectron && hasDefs && (
            <button onClick={runAuto} disabled={autoLoading || !hasDefs} style={{
              fontSize: 9, fontFamily: T.mono, padding: '2px 8px', borderRadius: T.radiusPill,
              cursor: (autoLoading || !hasDefs) ? 'not-allowed' : 'pointer',
              border: `1px solid rgba(99,200,120,0.35)`,
              background: autoLoading ? 'rgba(99,200,120,0.06)' : 'rgba(99,200,120,0.1)',
              color: autoLoading ? 'rgba(99,200,120,0.5)' : 'rgba(130,230,150,0.9)',
              opacity: hasDefs ? 1 : 0.4,
              transition: 'all 0.15s',
            }}>
              {autoLoading ? '…' : 'auto'}
            </button>
          )}
          <button
            onClick={custom ? resetToDefaults : (hasDefs ? enableCustom : null)}
            disabled={!hasDefs}
            style={{
              fontSize: 9, fontFamily: T.mono, padding: '2px 8px', borderRadius: T.radiusPill,
              cursor: hasDefs ? 'pointer' : 'not-allowed',
              border: `1px solid ${custom ? T.borderHover : T.border}`,
              background: custom ? T.accentSoft : 'transparent',
              color: custom ? T.accent : (hasDefs ? T.dim : T.dim),
              opacity: hasDefs ? 1 : 0.4,
              transition: 'all 0.15s',
            }}
          >
            {custom ? 'custom ✕' : 'override'}
          </button>
        </div>
      </div>

      {hasDefs && (
        <div style={{
          display: 'flex', gap: 8, marginBottom: custom ? 10 : 0,
          padding: '5px 8px', borderRadius: T.radiusSm,
          background: 'rgba(0,0,0,0.2)', border: `1px solid ${T.border}`,
        }}>
          <span style={{ fontSize: 10, color: T.dim, fontFamily: T.mono, flex: 1 }}>
            {custom ? 'default:' : 'active:'}
          </span>
          <span style={{ fontSize: 10, fontFamily: T.mono, color: custom ? T.dim : T.accent }}>
            m={fnDefs.m ?? '—'}
          </span>
          <span style={{ fontSize: 10, fontFamily: T.mono, color: custom ? T.dim : T.accent }}>
            β={fnDefs.beta ?? '—'}
          </span>
        </div>
      )}

      {!hasDefs && (
        <div style={{ fontSize: 10, color: T.dim, fontFamily: T.mono }}>
          {note || 'no m/β — function uses fixed math'}
        </div>
      )}

      {note && hasDefs && (
        <div style={{
          fontSize: 9, color: T.dim, fontFamily: T.mono,
          marginTop: custom ? 0 : 6, marginBottom: custom ? 8 : 0,
          opacity: 0.7, lineHeight: 1.5,
        }}>
          {note}
        </div>
      )}

      {autoNote && (
        <div style={{
          fontSize: 9, fontFamily: T.mono, lineHeight: 1.5, marginTop: 6, marginBottom: custom ? 6 : 0,
          padding: '4px 8px', borderRadius: T.radiusSm,
          background: autoNote.startsWith('auto failed') ? 'rgba(255,80,80,0.06)' : 'rgba(99,200,120,0.07)',
          border: `1px solid ${autoNote.startsWith('auto failed') ? 'rgba(255,80,80,0.15)' : 'rgba(99,200,120,0.18)'}`,
          color: autoNote.startsWith('auto failed') ? '#ff8080' : 'rgba(130,230,150,0.85)',
        }}>
          {autoNote}
        </div>
      )}

      {custom && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
          <ParamControl
            label="m — exponent (vertical pull)"
            value={params.m} min={0.0001} max={2} step={0.0001}
            onChange={set('m')} fmt={v => v.toFixed(4)}
          />
          <ParamControl
            label="β — lead amplitude"
            value={params.beta} min={0.0001} max={2} step={0.0001}
            onChange={set('beta')} fmt={v => v.toFixed(4)}
          />
        </div>
      )}
    </div>
  )
}

// ── Sidebar ────────────────────────────────────────────────────────────────
function Sidebar({ open, params, set, onGenerate, loading, isElectron, history, selectedHistory, onSelectHistory,
                   userFunctions, onOpenCustomLibrary }) {
  const groups   = [...new Set(FUNCTIONS.map(f => f.group))]
  const gridPts  = Math.ceil((params.xmax - params.xmin) / params.resolution)
               * Math.ceil((params.ymax - params.ymin) / params.resolution)
  const gridWarn = gridPts > 80000

  return (
    <div style={{
      width: open ? 280 : 0, minWidth: open ? 280 : 0,
      transition: 'width 0.26s cubic-bezier(0.4,0,0.2,1), min-width 0.26s cubic-bezier(0.4,0,0.2,1)',
      overflow: 'hidden', flexShrink: 0,
      borderRight: open ? `1px solid ${T.border}` : 'none',
      background: T.sidebar,
      backdropFilter: 'blur(40px)', WebkitBackdropFilter: 'blur(40px)',
      display: 'flex', flexDirection: 'column',
      position: 'relative', zIndex: 100,
    }}>
      <div style={{
        width: 280, minWidth: 280, height: '100%',
        display: 'flex', flexDirection: 'column',
        overflowY: 'auto', overflowX: 'hidden',
        opacity: open ? 1 : 0,
        transition: 'opacity 0.18s ease',
        pointerEvents: open ? 'auto' : 'none',
      }}>
        <div style={{ padding: '12px 10px 24px', display: 'flex', flexDirection: 'column', gap: 8 }}>

          {/* ── Section: Function & Normalization ── */}
          <Section title="Function & Normalization" defaultOpen={true}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 7 }}>
                <div style={{ flex: 1 }}><Label>Function</Label></div>
                <button onClick={onOpenCustomLibrary} style={{
                  fontSize: 9, fontFamily: T.mono, padding: '2px 8px', borderRadius: T.radiusPill,
                  border: `1px solid rgba(110,231,183,0.28)`,
                  background: 'rgba(110,231,183,0.06)', color: '#6ee7b7',
                  cursor: 'pointer', transition: 'all 0.15s', marginLeft: 6,
                }}>⊕ custom</button>
              </div>
              <select
                value={params.functionId}
                onChange={e => set('functionId')(e.target.value)}
                style={{
                  width: '100%', background: 'rgba(0,0,0,0.35)',
                  border: `1px solid ${T.border}`, color: T.text,
                  borderRadius: T.radiusSm, padding: '7px 10px', fontSize: 12,
                  fontFamily: T.mono, outline: 'none', cursor: 'pointer',
                }}
              >
                {groups.map(g => (
                  <optgroup key={g} label={g}>
                    {FUNCTIONS.filter(f => f.group === g).map(f => (
                      <option key={f.id} value={f.id} style={{ background: '#13112a' }}>
                        {f.id.padStart(2, ' ')}. {f.name}{f.broken ? ' ⚠' : ''}
                      </option>
                    ))}
                  </optgroup>
                ))}
                {userFunctions?.length > 0 && (
                  <optgroup label="My Functions">
                    {userFunctions.map(f => (
                      <option key={f.id} value={f.id} style={{ background: '#13112a' }}>
                        {f.id}. {f.name}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>
            <div>
              <Label>Normalization</Label>
              <div style={{ display: 'flex', gap: 6 }}>
                {[{ v: 'N', label: 'Raw' }, { v: 'Y', label: 'Normalized' }].map(({ v, label }) => {
                  const active = params.normalize === v
                  return (
                    <button key={v} onClick={() => set('normalize')(v)} style={{
                      flex: 1, padding: '6px 0', borderRadius: T.radiusSm, cursor: 'pointer',
                      border: active ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                      background: active ? T.accentSoft : 'rgba(0,0,0,0.2)',
                      color: active ? T.accent : T.muted,
                      fontWeight: active ? 600 : 400, fontSize: 12,
                      transition: 'all 0.15s', fontFamily: T.mono,
                    }}>
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
            <div>
              <Label>Im. Stretch</Label>
              <button
                onClick={() => set('colNormalize')(!params.colNormalize)}
                style={{
                  width: '100%', padding: '6px 0', borderRadius: T.radiusSm, cursor: 'pointer',
                  border: params.colNormalize ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                  background: params.colNormalize ? T.accentSoft : 'rgba(0,0,0,0.2)',
                  color: params.colNormalize ? T.accent : T.muted,
                  fontWeight: params.colNormalize ? 600 : 400, fontSize: 12,
                  transition: 'all 0.15s', fontFamily: T.mono,
                }}
              >
                {params.colNormalize ? 'on — equal hilliness' : 'off — raw amplitude'}
              </button>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
                <Label>Power Stretch</Label>
              </div>
              <button
                onClick={() => set('powerStretch')(params.powerStretch !== null ? null : 0.4)}
                style={{
                  width: '100%', padding: '6px 0', borderRadius: T.radiusSm, cursor: 'pointer',
                  border: params.powerStretch !== null ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                  background: params.powerStretch !== null ? T.accentSoft : 'rgba(0,0,0,0.2)',
                  color: params.powerStretch !== null ? T.accent : T.muted,
                  fontWeight: params.powerStretch !== null ? 600 : 400, fontSize: 12,
                  transition: 'all 0.15s', fontFamily: T.mono,
                  marginBottom: params.powerStretch !== null ? 8 : 0,
                }}
              >
                {params.powerStretch !== null ? `on — W^${params.powerStretch.toFixed(2)}` : 'off — no stretch'}
              </button>
              {params.powerStretch !== null && (
                <ParamControl
                  label="p  (1 = off · 0.4 = moderate · 0.1 = heavy)"
                  value={params.powerStretch}
                  min={0.05} max={1.0} step={0.01}
                  onChange={v => set('powerStretch')(Math.round(v * 100) / 100)}
                  fmt={v => v.toFixed(2)}
                />
              )}
            </div>
            <div>
              <Label>Plot Mode</Label>
              <div style={{ display: 'flex', gap: 6 }}>
                {[{ v: '3d', label: '3D Surface' }, { v: '2d', label: '2D Heatmap' }].map(({ v, label }) => {
                  const active = params.mode === v
                  return (
                    <button key={v} onClick={() => set('mode')(v)} style={{
                      flex: 1, padding: '6px 0', borderRadius: T.radiusSm, cursor: 'pointer',
                      border: active ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                      background: active ? T.accentSoft : 'rgba(0,0,0,0.2)',
                      color: active ? T.accent : T.muted,
                      fontWeight: active ? 600 : 400, fontSize: 12,
                      transition: 'all 0.15s', fontFamily: T.mono,
                    }}>
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
          </Section>

          {/* ── Section: Colormap ── */}
          <Section title="Colormap" defaultOpen={true}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {COLORMAPS.map(c => {
                const active = params.colormap === c.id
                return (
                  <button key={c.id} onClick={() => set('colormap')(c.id)} style={{
                    display: 'flex', flexDirection: 'column', gap: 5,
                    padding: '7px 10px', borderRadius: T.radiusSm, cursor: 'pointer',
                    border: active ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                    background: active ? T.accentSoft : 'rgba(0,0,0,0.15)',
                    transition: 'all 0.15s', textAlign: 'left',
                  }}>
                    <span style={{ fontSize: 11, color: active ? T.accent : T.muted, fontFamily: T.mono, fontWeight: active ? 600 : 400 }}>
                      {c.name}
                    </span>
                    <GradBar stops={c.stops} />
                  </button>
                )
              })}
            </div>
          </Section>

          {/* ── Section: Configuration ── */}
          <Section title="Configuration" defaultOpen={false}>

            {/* Resolution */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
                <Label>Resolution</Label>
                <span style={{
                  fontSize: 9, fontFamily: T.mono, padding: '2px 7px', borderRadius: T.radiusPill,
                  background: gridWarn ? 'rgba(251,191,36,0.1)' : 'rgba(180,160,255,0.08)',
                  color: gridWarn ? T.warn : T.dim,
                  border: `1px solid ${gridWarn ? 'rgba(251,191,36,0.2)' : T.border}`,
                }}>
                  ~{fmtCount(gridPts)} pts{gridWarn ? ' ⚠' : ''}
                </span>
              </div>
              <ParamControl
                label="Grid step — smaller = finer & slower"
                value={params.resolution} min={0.01} max={0.5} step={0.005}
                onChange={set('resolution')} fmt={v => v.toFixed(3)}
              />
            </div>

            <div style={{ height: 1, background: T.border, margin: '2px 0' }} />

            {/* Domain */}
            <div>
              <Label>Domain</Label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { key: 'xmin', label: 'X min' },
                  { key: 'xmax', label: 'X max' },
                  { key: 'ymin', label: 'Y min' },
                  { key: 'ymax', label: 'Y max' },
                ].map(({ key, label }) => (
                  <ParamControl key={key} label={label} value={params[key]}
                    min={-999} max={999} step={0.5}
                    onChange={set(key)} noSlider
                  />
                ))}
              </div>
            </div>

            <div style={{ height: 1, background: T.border, margin: '2px 0' }} />

            {/* View Angles — hidden in 2D mode */}
            {params.mode !== '2d' && (<>
            <div>
              <Label>View Angles</Label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <ParamControl label="Elevation" value={params.elev} min={0}    max={90}  step={1} onChange={set('elev')} fmt={v => `${v}°`} />
                <ParamControl label="Azimuth"   value={params.azim} min={-180} max={180} step={1} onChange={set('azim')} fmt={v => `${v}°`} />
              </div>
            </div>

            <div style={{ height: 1, background: T.border, margin: '2px 0' }} />
            </>)}

            {/* Coefficients */}
            <CoefficientsCard params={params} set={set} isElectron={isElectron} />

          </Section>

          {/* ── Section: History ── */}
          {history.length > 0 && (
            <Section title="History" defaultOpen={true}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 320, overflowY: 'auto' }}>
                {history.map(f => {
                  const active = selectedHistory?.path === f.path
                  return (
                    <button
                      key={f.path}
                      onClick={async () => {
                        const r = await window.electronAPI.getPlotData(f.path)
                        onSelectHistory({ ...f, dataUrl: r.dataUrl })
                      }}
                      style={{
                        padding: '6px 10px', borderRadius: T.radiusSm,
                        width: '100%', textAlign: 'left',
                        border: active ? `1px solid ${T.borderHover}` : `1px solid ${T.border}`,
                        background: active ? T.accentSoft : 'rgba(0,0,0,0.2)',
                        color: active ? T.accent : T.dim,
                        fontSize: 11, fontFamily: T.mono, cursor: 'pointer',
                        transition: 'all 0.15s',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}
                    >
                      {f.name}
                    </button>
                  )
                })}
              </div>
            </Section>
          )}

          {/* ── Generate ── */}
          <button onClick={onGenerate} disabled={loading} style={{
            padding: '11px 0', borderRadius: T.radius, cursor: loading ? 'not-allowed' : 'pointer',
            border: loading ? `1px solid ${T.border}` : '1px solid rgba(180,160,255,0.3)',
            background: loading ? 'rgba(0,0,0,0.2)' : 'linear-gradient(135deg, rgba(124,90,240,0.85), rgba(168,100,250,0.85))',
            boxShadow: loading ? 'none' : `0 0 24px ${T.accentGlow}, 0 2px 12px rgba(0,0,0,0.5)`,
            color: loading ? T.dim : '#fff',
            fontWeight: 700, fontSize: 13, letterSpacing: '0.06em',
            transition: 'all 0.2s',
          }}>
            {loading ? '⏳  Rendering…' : '▶  Generate Plot'}
          </button>

          {isElectron && (
            <button onClick={() => window.electronAPI.openOutputFolder()} style={{
              padding: '7px 0', borderRadius: T.radiusSm,
              border: `1px solid ${T.border}`, background: 'transparent',
              color: T.dim, fontSize: 10, cursor: 'pointer',
              fontFamily: T.mono, letterSpacing: '0.06em',
            }}>
              open output folder
            </button>
          )}

        </div>
      </div>
    </div>
  )
}

// ── Plot area ──────────────────────────────────────────────────────────────
function PlotArea({ result, loading, selectedHistory,
                    functionId, formulasMap, termsMap, userFunctions,
                    formulaOpen, onToggleFormula, formulaEditMode, onEnterFormulaEdit, onExitFormulaEdit,
                    onUserFnsChanged, isElectron }) {
  const shown = selectedHistory ?? result
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

      {/* Main plot */}
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: T.bg, position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          background: 'radial-gradient(ellipse 60% 50% at 50% 40%, rgba(100,70,200,0.055) 0%, transparent 70%)',
        }} />

        {!shown && !loading && (
          <div style={{ textAlign: 'center', color: T.dim, position: 'relative' }}>
            <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.45 }}>◈</div>
            <div style={{ fontSize: 12, color: T.muted, fontFamily: T.mono }}>select a function and generate</div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', position: 'relative' }}>
            <div style={{
              width: 36, height: 36, margin: '0 auto',
              border: `2px solid ${T.border}`, borderTopColor: T.accent,
              borderRadius: '50%', animation: 'spin 0.9s linear infinite',
            }} />
            <div style={{ fontSize: 11, marginTop: 14, fontFamily: T.mono, color: T.dim }}>computing surface…</div>
          </div>
        )}

        {shown?.error && !loading && (
          <div style={{
            padding: 24, maxWidth: 520,
            background: 'rgba(255,80,80,0.04)', border: '1px solid rgba(255,80,80,0.14)',
            borderRadius: T.radius,
          }}>
            <div style={{ fontWeight: 700, color: '#ff8080', marginBottom: 8, fontFamily: T.mono }}>render error</div>
            <pre style={{ fontSize: 10, color: '#cc6060', whiteSpace: 'pre-wrap', fontFamily: T.mono }}>{shown.error}</pre>
          </div>
        )}

        {shown?.dataUrl && !loading && (
          <img src={shown.dataUrl} alt={shown.name || 'Plot'}
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', position: 'relative' }}
          />
        )}
      </div>

      {/* Formula panel */}
      <FormulaPanel
        functionId={functionId}
        formulasMap={formulasMap}
        termsMap={termsMap}
        userFunctions={userFunctions}
        open={formulaOpen}
        onToggleOpen={onToggleFormula}
        editMode={formulaEditMode}
        onEnterEdit={onEnterFormulaEdit}
        onExitEdit={onExitFormulaEdit}
        onUserFnsChanged={onUserFnsChanged}
        isElectron={isElectron}
      />

      {/* Status bar */}
      <div style={{
        height: 24, background: 'rgba(5,5,14,0.96)',
        borderTop: `1px solid ${T.border}`,
        display: 'flex', alignItems: 'center',
        padding: '0 14px', gap: 12,
        fontSize: 10, fontFamily: T.mono, color: T.dim, flexShrink: 0,
      }}>
        {shown?.path
          ? <span style={{ opacity: 0.6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{shown.path}</span>
          : <span>no plot loaded</span>
        }
        {shown?.name && (
          <span style={{ color: T.accent, marginLeft: 'auto', flexShrink: 0 }}>{shown.name}</span>
        )}
      </div>
    </div>
  )
}

// ── App ────────────────────────────────────────────────────────────────────
export default function App() {
  const [params, setParams]                   = useState(DEFAULT_PARAMS)
  const [loading, setLoading]                 = useState(false)
  const [result,  setResult]                  = useState(null)
  const [history, setHistory]                 = useState([])
  const [selectedHistory, setSelectedHistory] = useState(null)
  const [isElectron, setIsElectron]           = useState(false)
  const [sidebarOpen, setSidebarOpen]         = useState(true)
  const [userFunctions,   setUserFunctions]   = useState([])
  const [formulasMap,     setFormulasMap]     = useState({})
  const [termsMap,        setTermsMap]        = useState({})
  const [formulaOpen,     setFormulaOpen]     = useState(true)
  const [formulaEditMode, setFormulaEditMode] = useState(false)

  useEffect(() => { setIsElectron(!!window.electronAPI) }, [])

  useEffect(() => {
    if (!isElectron) return
    window.electronAPI.listPlots().then(r => { if (r.success) setHistory(r.files) })
    window.electronAPI.getAllFormulas().then(r => {
      if (r.success) { setFormulasMap(r.formulas || {}); setTermsMap(r.terms || {}) }
    })
    window.electronAPI.listUserFunctions().then(r => { if (r.success) setUserFunctions(r.functions) })
  }, [isElectron])

  const reloadUserFunctions = useCallback(() => {
    if (!isElectron) return
    window.electronAPI.listUserFunctions().then(r => { if (r.success) setUserFunctions(r.functions) })
  }, [isElectron])

  const openCustomLibrary = useCallback(() => {
    setFormulaOpen(true)
    setFormulaEditMode(true)
  }, [])

  const set = key => val => setParams(p => ({ ...p, [key]: val }))

  const generate = useCallback(async () => {
    if (!isElectron) return
    setLoading(true); setResult(null); setSelectedHistory(null)
    try {
      const r = await window.electronAPI.generatePlot(params)
      if (r.success) {
        setResult({ path: r.path, name: r.name, dataUrl: r.dataUrl })
        const hr = await window.electronAPI.listPlots()
        if (hr.success) setHistory(hr.files)
      } else {
        setResult({ error: r.error || r.trace })
      }
    } finally {
      setLoading(false)
    }
  }, [params, isElectron])

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100vh',
      background: T.bg, color: T.text, overflow: 'hidden',
      fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
    }}>
      <TitleBar sidebarOpen={sidebarOpen} onToggle={() => setSidebarOpen(v => !v)} isElectron={isElectron} />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        <Sidebar
          open={sidebarOpen}
          params={params}
          set={set}
          onGenerate={generate}
          loading={loading}
          isElectron={isElectron}
          history={history}
          selectedHistory={selectedHistory}
          onSelectHistory={h => { setSelectedHistory(h); setResult(null) }}
          userFunctions={userFunctions}
          onOpenCustomLibrary={openCustomLibrary}
        />
        <PlotArea
          result={result}
          loading={loading}
          selectedHistory={selectedHistory}
          functionId={params.functionId}
          formulasMap={formulasMap}
          termsMap={termsMap}
          userFunctions={userFunctions}
          formulaOpen={formulaOpen}
          onToggleFormula={() => setFormulaOpen(v => !v)}
          formulaEditMode={formulaEditMode}
          onEnterFormulaEdit={() => { setFormulaOpen(true); setFormulaEditMode(true) }}
          onExitFormulaEdit={() => setFormulaEditMode(false)}
          onUserFnsChanged={reloadUserFunctions}
          isElectron={isElectron}
        />
      </div>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${T.bg}; overflow: hidden; }
        ::-webkit-scrollbar       { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${T.dim}; border-radius: 4px; }
        select option, select optgroup { background: #100e24; color: #edeaf8; }
        input[type=range] { height: 3px; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── KaTeX syntax-colouring ── */
        /* Operators: ∏ ∑ + − · = < > sin cos tan */
        .katex .mop  { color: #6ee7b7; }
        .katex .mbin { color: #6ee7b7; }
        .katex .mrel { color: #86efac; }
        /* Variables / italic letters (z, x, k, n, m) */
        .katex .mord.mi, .katex .mord.mathnormal { color: #93c5fd; }
        /* Numbers */
        .katex .mord.mn { color: #e2e8f0; }
        /* Delimiters / brackets / |·| */
        .katex .mopen, .katex .mclose { color: #c4b5fd; }
        /* Fraction bar */
        .katex .frac-line { background-color: #6ee7b7 !important; }
        /* Floor/ceil brackets */
        .katex .minner { color: inherit; }
        /* Display-mode formula: scale up in the panel */
        .formula-panel .katex-display { margin: 0; }
        .formula-panel .katex { font-size: 1.65em; }
      `}</style>
    </div>
  )
}
