import math



features = [
    ('tightMuons_pt', lambda event, syst: getattr(event,"tightMuons_pt")[0]),
    ('tightMuons_charge', lambda event, syst: math.fabs(getattr(event,"tightMuons_charge")[0])),
    
    ('nominal_mtw', lambda event, syst: getattr(event,"nominal_mtw")),
    ('nominal_met', lambda event, syst: getattr(event,"nominal_met")),
    ('nominal_met_lepton_deltaPhi', lambda event, syst: math.fabs(getattr(event,"nominal_met_lepton_deltaPhi"))),
    ('nominal_eventShape_C', lambda event, syst: getattr(event,"nominal_eventShape_C")),
    ('nominal_ljet_eta', lambda event, syst: math.fabs(getattr(event,"nominal_ljet_eta"))),
    ('nominal_bjet_lepton_deta', lambda event, syst: math.fabs(getattr(event,"nominal_bjet_lepton_deta"))),
    ('nominal_ljet_bjet_dR', lambda event, syst: getattr(event,"nominal_ljet_bjet_dR")),
    ('nominal_wboson_cosHelicity', lambda event, syst: getattr(event,"nominal_wboson_cosHelicity")),
    ('nominal_top_cosPolarization', lambda event, syst: getattr(event,"nominal_top_cosPolarization")),
    ('nominal_top_mass', lambda event, syst: getattr(event,"nominal_top_mass")),
    ('nominal_top_pt', lambda event, syst: getattr(event,"nominal_top_pt")),
]

