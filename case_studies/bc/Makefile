# Definition options
CENSE_OPTIONS = CSCO CSCLE CLEO
PERSE_OPTIONS = CSKS CEKS CLKS
CENKS_OPTIONS = PSCO PSCLE PLEO
PERKS_OPTIONS = PSKS PEKS PLKS

OUTPUT_DIR = BC_SESSION_MODELS
OUTPUT_NAME = BC_SESSION
TYPE = QA SA
QA_TEMPLATE = templates/bc_session_QA_template.m4
SA_TEMPLATE = templates/bc_session_SA_template.m4

COMBO_QA := $(foreach d1,$(CENSE_OPTIONS), \
          $(foreach d2,$(PERSE_OPTIONS), \
          $(foreach d3,$(CENKS_OPTIONS), \
          $(foreach d4,$(PERKS_OPTIONS), \
          $(if $(filter $(d1)-$(d3),CSCO-PLEO CLEO-PSCO),, \
          $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_$(d1)_$(d2)_$(d3)_$(d4).spthy)))))

COMBO_SA := $(foreach d1,$(CENSE_OPTIONS), \
          $(foreach d2,$(PERSE_OPTIONS), \
          $(foreach d3,$(CENKS_OPTIONS), \
          $(foreach d4,$(PERKS_OPTIONS), \
          $(if $(filter $(d1)-$(d3),CSCO-PLEO CLEO-PSCO),,\
          $(OUTPUT_DIR)/$(OUTPUT_NAME)_SA_$(d1)_$(d2)_$(d3)_$(d4).spthy)))))

COMBO := \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CLEO_CEKS_PLEO_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CSCLE_CSKS_PSCLE_PEKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_SA_CLEO_CSKS_PLEO_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CLEO_CLKS_PLEO_PEKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CSCLE_CSKS_PSCLE_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_SA_CSCLE_CSKS_PSCLE_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CLEO_CLKS_PLEO_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CSCO_CSKS_PSCO_PEKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_SA_CSCO_CSKS_PSCO_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CLEO_CSKS_PLEO_PLKS.spthy \
    $(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_CSCO_CSKS_PSCO_PLKS.spthy

# Default target
all: $(OUTPUT_DIR) $(COMBO)
# QA
QA: $(OUTPUT_DIR) $(COMBO_QA) 
# SA
SA: $(OUTPUT_DIR) $(COMBO_SA) 


$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Rule to generate each output file
$(OUTPUT_DIR)/$(OUTPUT_NAME)_QA_%.spthy: $(OUTPUT_DIR) $(TEMPLATE)
	@D1=$(word 1, $(subst _, ,$*)) \
	D2=$(word 2, $(subst _, ,$*)) \
	D3=$(word 3, $(subst _, ,$*)) \
	D4=$(word 4, $(subst _, ,$*)) ; \
	echo "Generating file: $@"; \
	m4 -D$$D1 -D$$D2 -D$$D3 -D$$D4 $(QA_TEMPLATE) > $@.tmp
	@cd ../.. && python3 ./entropy_verif/main.py case_studies/bc/$@.tmp -o case_studies/bc/$@ --derive-level=3 --propagate-level=3 && cd case_studies/bc
	@rm $@.tmp

$(OUTPUT_DIR)/$(OUTPUT_NAME)_SA_%.spthy: $(OUTPUT_DIR) $(TEMPLATE)
	@D1=$(word 1, $(subst _, ,$*)) \
	D2=$(word 2, $(subst _, ,$*)) \
	D3=$(word 3, $(subst _, ,$*)) \
	D4=$(word 4, $(subst _, ,$*)) ; \
	echo "Generating file: $@"; \
	m4 -D$$D1 -D$$D2 -D$$D3 -D$$D4 $(SA_TEMPLATE) > $@.tmp
	@cd ../..  && python3 ./entropy_verif/main.py case_studies/bc/$@.tmp -o case_studies/bc/$@ --derive-level=3 --propagate-level=3 && cd case_studies/bc
	@rm $@.tmp


# Clean up all generated files and directories
clean:
	rm -rf $(OUTPUT_DIR)
