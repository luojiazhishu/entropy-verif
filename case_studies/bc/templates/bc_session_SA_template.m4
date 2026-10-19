dnl ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
divert(-1)
changequote(<!,!>)
define(M4_CENTRAL_SC_FEAT, <!dnl
ifdef(<!CSCO!>, TRUE, 
ifdef(<!CSCLE!>, TRUE, 
ifdef(<!CLEO!>, FALSE,
    UNKNOW_SECURE_MODE)))!>)

define(M4_CENTRAL_SC_MODE, <!dnl
ifdef(<!CSCO!>, SC_Only, 
ifdef(<!CSCLE!>, SC_Legacy, 
ifdef(<!CLEO!>, Legacy_Only,
    UNKNOW_SECURE_MODE)))!>)

define(M4_CENTRAL_KS_MODE, <!dnl
ifdef(<!CSKS!>, Secure_Key_Size, 
ifdef(<!CEKS!>, Enhanced_Key_Size, 
ifdef(<!CLKS!>, Legacy_Key_Size,
    UNKNOW_KEY_SIZE)))!>)

define(M4_PERIPHERAL_SC_FEAT, <!dnl
ifdef(<!PSCO!>, TRUE, 
ifdef(<!PSCLE!>, TRUE, 
ifdef(<!PLEO!>, FALSE,
    UNKNOW_SECURE_MODE)))!>)

define(M4_PERIPHERAL_SC_MODE, <!dnl
ifdef(<!PSCO!>, SC_Only, 
ifdef(<!PSCLE!>, SC_Legacy, 
ifdef(<!PLEO!>, Legacy_Only,
    UNKNOW_SECURE_MODE)))!>)

define(M4_PERIPHERAL_KS_MODE, <!dnl
ifdef(<!PSKS!>, Secure_Key_Size, 
ifdef(<!PEKS!>, Enhanced_Key_Size, 
ifdef(<!PLKS!>, Legacy_Key_Size,
    UNKNOW_KEY_SIZE)))!>)

divert(0)dnl
dnl ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#{/*****************************************************************
* Secure Mode:
*     - SC_Only
*     - SC_Legacy
*     - Legacy_Only
* 
* Key Size:
*     - Secure_Key_Size
*     - Enhanced_Key_Size
*     - Legacy_Key_Size
* 
* Central Device (CEN):
*     - M4_CENTRAL_KS_MODE()
*     - M4_CENTRAL_SC_MODE()
* 
* Peripheral Device (PER):
*     - M4_PERIPHERAL_KS_MODE()
*     - M4_PERIPHERAL_SC_MODE()
* 
* Adversary: SA 
*****************************************************************/#}


theory BC_Session_Establishment

begin 
builtins: symmetric-encryption
functions: E1/3, E3/3, h3/5, h4/4, h5/3,
    resize/2, left/1, right/1, N1/0, N2/0, N3/0, N4/0,
    TRUE/0, FALSE/0, 
    SelectKS/2, SelectAU/2, SECURE_AU/0, LEGACY_AU/0
    
equations:
    SelectAU(x, FALSE) = LEGACY_AU,
    SelectAU(FALSE, x) = LEGACY_AU,
    SelectAU(TRUE, TRUE) = SECURE_AU,

    SelectKS(x, x) = x,
    SelectKS(N1, x) = N1,
    SelectKS(x, N1) = N1,
    SelectKS(N2, N3) = N2,
    SelectKS(N3, N2) = N2,
    SelectKS(x, N4) = x,
    SelectKS(N4, x) = x,

    resize(m, N1) = left(left(m)),
    resize(m, N2) = combine(left(left(m)), right(left(m))),
    resize(m, N3) = combine(combine(left(left(m)), right(left(m))), left(right(m))),
    resize(m, N4) = combine(combine(left(left(m)), right(left(m))), combine(left(right(m)), right(right(m))))


#{/****************************************************
*   Pairing                                         *
****************************************************/#}
rule PairDevices [color=#bdb5e1]:
    let
        CKeysize = N4
        CFeatureSC = M4_CENTRAL_SC_FEAT()
        CSecureMode = 'M4_CENTRAL_SC_MODE()'
        CKeysizeMode = 'M4_CENTRAL_KS_MODE()'
        PKeysize = N4
        PFeatureSC = M4_PERIPHERAL_SC_FEAT()
        PSecureMode = 'M4_PERIPHERAL_SC_MODE()'
        PKeysizeMode = 'M4_PERIPHERAL_KS_MODE()'
    in 
    [
        Fr(~LK)
    ]
    --[ OnlyOnceV(<'PairDevices'>) ]->
    [
        !CentralDevice('Paired', <$CEN, CKeysize, CFeatureSC, CSecureMode, CKeysizeMode, ~LK, $PER>),
        !PeripheralDevice('Paired', <$PER, PKeysize, PFeatureSC, PSecureMode, PKeysizeMode, ~LK, $CEN>)
    ]

#{/****************************************************
*   Feature Exchange                                *
****************************************************/#}
#{
    predicates:
        VaildAuthMethod(mode, feat, method)  <=>  
            (feat = TRUE | feat = FALSE) &
            (mode = 'SC_Legacy' | mode = 'SC_Only' & method = SECURE_AU | mode = 'Legacy_Only' & method = LEGACY_AU)
#}

rule CenSendFeaturesReq [color=#b0d992]:
    [
        !CentralDevice('Paired', <$CEN, CKeysize, CFeatureSC, CSecureMode, CKeysizeMode, LK, $PER>),
    ] 
    --> 
    [
        StateCen('FeatReqSent', <$CEN, CKeysize, CFeatureSC, CSecureMode, CKeysizeMode, LK, $PER>),
        Out(<$CEN, $PER, 'FeatReq', CFeatureSC>)
    ]

rule PerRecvFeaturesReq [color=#99b9e9]:
    let
        AuMethod = SelectAU(CFeatureSC, PFeatureSC) 
    in
    [
        In(<$CEN, $PER, 'FeatReq', CFeatureSC>),
        !PeripheralDevice('Paired', <$PER, PKeysize, PFeatureSC, PSecureMode, PKeysizeMode, LK, $CEN>)
    ] 
    --[_restrict(VaildAuthMethod(PSecureMode, CFeatureSC, AuMethod))]->
    [
        StatePer('FeatExchanged', <$PER, PKeysize, PKeysizeMode, LK, AuMethod, $CEN>),
        Out(<$PER, $CEN, 'FeatRsp', PFeatureSC>)
    ]

rule CenRecvFeaturesRsp [color=#b0d992]:
    let
        AuMethod = SelectAU(CFeatureSC, PFeatureSC) 
    in 
    [
        In(<$PER, $CEN, 'FeatRsp', PFeatureSC>),
        StateCen('FeatReqSent', <$CEN, CKeysize, CFeatureSC, CSecureMode, CKeysizeMode, LK, $PER>),
    ]
    --[_restrict(VaildAuthMethod(CSecureMode, PFeatureSC, AuMethod))]->
    [
        StateCen('FeatExchanged', <$CEN, CKeysize, CKeysizeMode, LK, AuMethod, $PER>),
    ]

#{/****************************************************
*   Legacy Authentication                           *
****************************************************/#}
rule CenLegacySendAuRand [color=#b0d992]:
    [
        Fr(~AuRand),
        StateCen('FeatExchanged', <$CEN, CKeysize, CKeysizeMode, LK, LEGACY_AU, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'AU_RAND', ~AuRand>),
        StateCen('AuRandSent', <$CEN, CKeysize, CKeysizeMode, LK, LEGACY_AU, ~AuRand, $PER>)
    ]

rule PerLegacyRecvAuRand [color=#99b9e9]:
    let
        SRES = fst(E1(LK, AuRand, $B))
        ACO = snd(E1(LK, AuRand, $B))
    in [
        In(<$CEN, $PER, 'AU_RAND', AuRand>),
        StatePer('FeatExchanged', <$PER, PKeysize, PKeysizeMode, LK, LEGACY_AU, $CEN>)
    ] 
    --[]->
    [
        Out(<$PER, $CEN, 'SRES', SRES>),
        StatePer('AuthFinished', <$PER, PKeysize, PKeysizeMode, LK, LEGACY_AU, ACO, $CEN>)
    ]

rule CenLegacyRecvSERS [color=#b0d992]:
    let
        SRES = fst(E1(LK, ~AuRand, $PER))
        ACO = snd(E1(LK, ~AuRand, $PER))
    in [
        In(<$PER, $CEN, 'SRES', SRES>),
        StateCen('AuRandSent', <$CEN, CKeysize, CKeysizeMode, LK, LEGACY_AU, ~AuRand, $PER>)
    ]
    --[]->
    [
        StateCen('AuthFinished', <$CEN, CKeysize, CKeysizeMode, LK, LEGACY_AU, ACO, $PER>)
    ]

#{/****************************************************
*   Secure Authentication                           *
****************************************************/#}
rule CenSecureSendAuRand [color=#b0d992]:
    [
        Fr(~AuRandC),
        StateCen('FeatExchanged', <$CEN, CKeysize, CKeysizeMode, LK, SECURE_AU, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'AU_RAND', ~AuRandC>),
        StateCen('AuRandSent', <$CEN, CKeysize, CKeysizeMode, LK, SECURE_AU, ~AuRandC, $PER>)
    ]


rule PerSecureRecvAuRand [color=#99b9e9]:
    let
        DAK = h4(LK, 'btdk', $CEN, $PER)
        SERS = fst(h5(DAK, AuRandC, ~AuRandP))
        SERS_C = fst(SERS)
        SERS_P = snd(SERS)
        ACO = snd(h5(DAK, AuRandC, ~AuRandP))
    in
    [
        Fr(~AuRandP),
        In(<$CEN, $PER, 'AU_RAND', AuRandC>),
        StatePer('FeatExchanged', <$PER, PKeysize, PKeysizeMode, LK, SECURE_AU, $CEN>)
    ]
    --[]->
    [
        Out(<$PER, $CEN, 'AU_RAND', ~AuRandP>),
        Out(<$PER, $CEN, 'SRES', SERS_P>),
        StatePer('SRESSent', <$PER, PKeysize, PKeysizeMode, LK, SECURE_AU, ACO, $CEN, SERS_C>)
    ]

rule CenSecureRecvAuRand [color=#b0d992]:
    let
        DAK = h4(LK, 'btdk', $CEN, $PER)
        SERS = fst(h5(DAK, ~AuRandC, AuRandP))
        SERS_C = fst(SERS)
        SERS_P = snd(SERS)
        ACO = snd(h5(DAK, ~AuRandC, AuRandP))
    in
    [
        In(<$PER, $CEN, 'AU_RAND', AuRandP>),
        In(<$PER, $CEN, 'SRES', SERS_P>),
        StateCen('AuRandSent', <$CEN, CKeysize, CKeysizeMode, LK, SECURE_AU, ~AuRandC, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'SRES', SERS_C>),
        StateCen('AuthFinished', <$CEN, CKeysize, CKeysizeMode, LK, SECURE_AU, ACO, $PER>)
    ]

rule PerSecureVerifySERS [color=#99b9e9]:
    [
        In(<$CEN, $PER, 'SRES', SERS_C>),
        StatePer('SRESSent', <$PER, PKeysize, PKeysizeMode, LK, SECURE_AU, ACO, $CEN, SERS_C>)
    ]
    --[]->
    [
        StatePer('AuthFinished', <$PER, PKeysize, PKeysizeMode, LK, SECURE_AU, ACO, $CEN>)
    ]

#{/****************************************************
*   Key Size Negotiation                            *
****************************************************/#}
#{
    predicates:
        VaildKeySize(mode, keysize) <=> (keysize = N1 | keysize = N2 | keysize = N3 | keysize = N4) & (
            mode = 'Legacy_Key_Size' | 
            mode = 'Enhanced_Key_Size' & (not keysize = N1) | 
            mode = 'Secure_Key_Size' & keysize = N4
        )
#}

rule CenSendKeysizeReq [color=#b0d992]:
    [
        StateCen('AuthFinished', <$CEN, CKeysize, CKeysizeMode, LK, AuMethod, ACO, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'KEYSIZE', CKeysize>),
        StateCen('KeysizeSent', <$CEN, CKeysize, CKeysizeMode, LK, AuMethod, ACO, $PER>)
    ]

rule PerSendKeysizeReq [color=#99b9e9]:
    let
        keysize = SelectKS(CKeysize, PKeysize)
    in
    [
        In(<$CEN, $PER, 'KEYSIZE', CKeysize>),
        StatePer('AuthFinished', <$PER, PKeysize, PKeysizeMode, LK, AuMethod, ACO, $CEN>)
    ]
    --[_restrict(VaildKeySize(PKeysizeMode, keysize))]->
    [
        Out(<$PER, $CEN, 'KEYSIZE', PKeysize>),
        StatePer('KeysizeSent', <$PER, LK, AuMethod, ACO, keysize, $CEN>)
    ]

rule CenRecvKeysizeReq [color=#b0d992]:
    let
        KeySize = SelectKS(CKeysize, PKeysize)
    in
    [
        In(<$PER, $CEN, 'KEYSIZE', PKeysize>),
        StateCen('KeysizeSent', <$CEN, CKeysize, CKeysizeMode, LK, AuMethod, ACO, $PER>)
    ]
    --[_restrict(VaildKeySize(CKeysizeMode, KeySize))]->
    [
        Out(<$CEN, $PER, 'ACCEPTED'>),
        StateCen('KeysizeNegotiated', <$CEN, LK, AuMethod, ACO, KeySize, $PER>)
    ]

rule PerRecvKeysizeAccept [color=#99b9e9]:
    [
        In(<$CEN, $PER, 'ACCEPTED'>),
        StatePer('KeysizeSent', <$PER, LK, AuMethod, ACO, KeySize, $CEN>)
    ]
    --[]->
    [
        StatePer('KeysizeNegotiated', <$PER, LK, AuMethod, ACO, KeySize, $CEN>)
    ]

#{/****************************************************
*   Legacy Distrubute Session Key                   *
****************************************************/#}
rule CenLegacyEncReq [color=#b0d992]:
    let (
        L := `L`,
        R := `L`,
        LL := `L`,
        LR := `L`,
        RL := `L`,
        RR := `L`
    )
        SKFull = E3(LK, ~EnRand, ACO)
        SK = resize(SKFull, KeySize)
        L = combine(left(left(SKFull)), right(left(SKFull)))
        R = combine(left(right(SKFull)), right(right(SKFull)))
        LL = left(left(SKFull))
        LR = right(left(SKFull))
        RL = left(right(SKFull))
        RR = right(right(SKFull))
    in
    [
        Fr(~EnRand),
        StateCen('KeysizeNegotiated', <$CEN, LK, LEGACY_AU, ACO, KeySize, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'ENC_REQ', ~EnRand>),
        StateCen('EnRandSent', <$CEN, LK, LEGACY_AU, SK, $PER>)
    ]

rule PerLegacyEncRsp [color=#99b9e9]:
    let (
        L := `L`,
        R := `L`,
        LL := `L`,
        LR := `L`,
        RL := `L`,
        RR := `L`
    )
        SKFull = E3(LK, EnRand, ACO)
        SK = resize(SKFull, KeySize)
        L = combine(left(left(SKFull)), right(left(SKFull)))
        R = combine(left(right(SKFull)), right(right(SKFull)))
        LL = left(left(SKFull))
        LR = right(left(SKFull))
        RL = left(right(SKFull))
        RR = right(right(SKFull))
    in
    [
        In(<$CEN, $PER, 'ENC_REQ', EnRand>),
        StatePer('KeysizeNegotiated', <$PER, LK, LEGACY_AU, ACO, KeySize, $CEN>)
    ]
    --[ 
        PeripheralSKInstalled($PER, $CEN, SK)
    ]->
    [
        Out(<$PER, $CEN, senc('ACCEPTED', SK)>),
        StatePer('EncStarted', <$PER, LK, LEGACY_AU, SK, $CEN>)
    ]

#{/****************************************************
*   SC Calculate Session Key                        *
****************************************************/#}
// EnRand is no longer used in SC, but it's still remained.
rule CenSCEncReq [color=#b0d992]: 
    let (
        L := `L`,
        R := `L`,
        LL := `L`,
        LR := `L`,
        RL := `L`,
        RR := `L`
    )
        SKFull = h3(LK, 'btak', $CEN, $PER, ACO)
        SK = resize(SKFull, KeySize)
        L = combine(left(left(SKFull)), right(left(SKFull)))
        R = combine(left(right(SKFull)), right(right(SKFull)))
        LL = left(left(SKFull))
        LR = right(left(SKFull))
        RL = left(right(SKFull))
        RR = right(right(SKFull))
    in
    [
        Fr(~EnRand),
        StateCen('KeysizeNegotiated', <$CEN, LK, SECURE_AU, ACO, KeySize, $PER>)
    ]
    --[]->
    [
        Out(<$CEN, $PER, 'ENC_REQ', ~EnRand>),
        StateCen('EnRandSent', <$CEN, LK, SECURE_AU, SK, $PER>)
    ]

rule PerSCEncRsp [color=#99b9e9]:
    let (
        L := `L`,
        R := `L`,
        LL := `L`,
        LR := `L`,
        RL := `L`,
        RR := `L`
    )
        SKFull = h3(LK, 'btak', $CEN, $PER, ACO)
        SK = resize(SKFull, KeySize)
        L = combine(left(left(SKFull)), right(left(SKFull)))
        R = combine(left(right(SKFull)), right(right(SKFull)))
        LL = left(left(SKFull))
        LR = right(left(SKFull))
        RL = left(right(SKFull))
        RR = right(right(SKFull))
    in
    [
        In(<$CEN, $PER, 'ENC_REQ', EnRand>),
        StatePer('KeysizeNegotiated', <$PER, LK, SECURE_AU, ACO, KeySize, $CEN>)
    ]
    --[ 
        PeripheralSKInstalled($PER, $CEN, SK)
    ]->
    [
        Out(<$PER, $CEN, senc('ACCEPTED', SK)>),
        StatePer('EncStarted', <$PER, LK, SECURE_AU, SK, $CEN>)
    ]

#{/****************************************************
*   Encryption Start                                *
****************************************************/#}
rule CenFinished [color=#b0d992]:
    [
        In(<$PER, $CEN, senc('ACCEPTED', SK)>),
        StateCen('EnRandSent', <$CEN, LK, AuMethod, SK, $PER>)
    ]
    --[ 
        CentralSKInstalled($CEN, $PER, SK)
    ]->
    [
        Out(<$CEN, $PER, senc('APPLICATION_DATA', SK)>),
        StateCen('EncStarted', SK)
    ]

rule PerFinished [color=#99b9e9]:
    [
        In(<$CEN, $PER, senc('APPLICATION_DATA', SK)>),
        StatePer('EncStarted', <$PER, LK, AuMethod, SK, $CEN>)
    ]
    --[ 
        Finish($CEN, $PER)
    ]->
    [
        StatePer('Finished', SK)
    ]

#{
restriction OnlyOnceV:
    "All #i #j x. OnlyOnceV(x)@#i & OnlyOnceV(x)@#j ==> #i = #j"

tactic: BCtactic
    presort: S
    prio:
        regex ".*MR.*"
    prio:
        regex ".*CentralSKInstalled.*"
    prio:
        regex ".*PeripheralSKInstalled.*"
    prio:
        regex ".*PerCommit.*"
    prio:
        regex ".*CenCommit.*"
    prio:
        regex ".*CenRunning.*"
    prio:
        regex ".*PerRunning.*"
    prio:
        regex ".*State.*"
    prio:
        regex ".*KU\(\s~LK.*"
    prio:
        regex ".*KU\(\sE1.*"
    prio:
        regex ".*KU\(\sE3.*"
    prio:
        regex ".*KU\(\sh3.*"
    prio:
        regex ".*KU\(\sh4.*"
    prio:
        regex ".*KU\(\sh5.*"
    prio:
        regex ".*KU\(\sfst.*"
    prio:
        regex ".*KU\(\ssnd.*"
    prio:
        regex ".*KU\(\ssenc.*"
    prio:
        regex ".*KU\(\s~.*"
    prio:
        regex ".*KU\(\scombine\(\s*~LK.*"
    prio:
        regex ".*KU\(\scombine\(.*,\s*~LK\s*\)\s*\)[^\)]*#"
    prio:
        regex ".*KU\(\scombine\(h\d\(~LK.*"
    prio:
        regex ".*KU\(\scombine\(E\d\(~LK.*"
    prio:
        regex ".*KU\(\scombine\(~.*"
    prio:
        regex ".*KU\(\scombine\(.*,\s*~[^,\s\(\)]+\s*\)\s*\)[^\)]*#"
    prio:
        regex ".*KU\(\s(?!combine|left|right).*"
    deprio:
        regex ".*EntropyLow.*"
    deprio:
        regex ".*MDerive\d\(.*combine.*"
    deprio:
        regex ".*MDerive\d\(.*left.*"
    deprio:
        regex ".*MDerive\d\(.*right.*"
    deprio:
        regex ".*MDerive0\(.*"
    deprio:
        regex ".*MDerive1\(.*"
    deprio:
        regex ".*KU\(\scombine.*"
    deprio:
        regex ".*KU\(\sright\(E3.*"
    deprio:
        regex ".*KU\(\sleft\(E3.*"
    deprio:
        regex ".*KU\(\sright\(h3.*"
    deprio:
        regex ".*KU\(\sleft\(h3.*"
    deprio:
        regex ".*KU\(\sright\(right.*"
    deprio:
        regex ".*KU\(\sleft\(right.*"
    deprio:
        regex ".*KU\(\sright\(left.*"
    deprio:
        regex ".*KU\(\sleft\(left.*"
    deprio:
        regex ".*=.*"
    deprio:
        regex ".*splitEqs.*"

        
lemma Executable [heuristic={BCtactic}]:
    exists-trace
    "Ex C P SK #i #j #k. PeripheralSKInstalled(P, C, SK)@i & CentralSKInstalled(C, P, SK) @j & Finish(C, P)@k"

lemma SecrecyCentralSK [heuristic={BCtactic}]:
    "All C P SK #i. CentralSKInstalled(C, P, SK)@i ==> not (Ex #j. K(SK)@j)"

lemma SecrecyPeriheralSK [heuristic={BCtactic}]:
    "All C P SK #i. PeripheralSKInstalled(P, C, SK)@i ==> not (Ex #j. K(SK)@j)"

lemma MITMResistance [heuristic={BCtactic}]:
    "All C P SK1 SK2 #i #j.  CentralSKInstalled(C, P, SK1)@i & PeripheralSKInstalled(P, C, SK2)@j ==> not (Ex #k1 #k2. K(SK1)@k1 & K(SK2)@k2)"

#}

end
changequote
