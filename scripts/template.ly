\version "2.24.0"
\pointAndClickOff

\header {
    title = "TITLE"
    source =
    "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"
    tagline = \markup { \center-column {
        "Digitalizované doprovody k Mešním zpěvům https://github.com/olin256/mesni-zpevy"
        \concat { "Podle " \italic "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve" }
        \italic "a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"
    } }
    }

\paper {
     markup-system-spacing.basic-distance = #10
}

\layout {
    indent = #0
    \context { \Score
        autoBeaming = ##f
        \override SpacingSpanner.spacing-increment = 2.4
        % TIME
    }
    \context { \Staff
        \consists Merge_rests_engraver
    }
}


% VOICES

\score {
    << \new PianoStaff
        <<
            \context Staff = "top" <<
                \soprano \\ \alto
            >> \context Staff = "bottom" <<
                \tenor \\ \bass
            >>
        >>
    >>
    \layout {}
}