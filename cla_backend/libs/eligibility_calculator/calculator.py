from . import constants


class CapitalCalculator(object):
    def __init__(self, properties=[], liquid_capital=0):
        self.properties = self._parse_props(properties)
        self.liquid_capital = liquid_capital

    def _parse_props(self, props):
        l = []
        for p in (props or []):
            parsed_prop = p.copy()
            parsed_prop['equity'] = 0
            l.append(parsed_prop)
        return l

    @property
    def main_property(self):
        if not self.properties:
            return None
        return self.properties[0]

    @property
    def other_properties(self):
        if not self.properties:
            return []
        return self.properties[1:]

    # for each other property
    def _calculate_property_equity(self, prop):
        mortgage_disregard = min(prop['mortgage_left'], self.mortgage_disregard_available)

        property_equity = prop['value'] - mortgage_disregard
        # if prop.in_joint_names:
        property_equity = property_equity * prop['share'] / 100   # assuming that you filled in share with the right figure (that is, in_joint_names not required)

        remaining_mortgage_disregard = self.mortgage_disregard_available - mortgage_disregard

        prop['equity'] = max(property_equity, 0)
        self.mortgage_disregard_available = remaining_mortgage_disregard

    def _apply_SMOD_disregard(self, prop):
        if not prop['disputed']:
            return

        SMOD_disregard = min(prop['equity'], self.SMOD_disregard_available)

        prop['equity'] = max(prop['equity'] - SMOD_disregard, 0)
        remaining_SMOD_disregard = self.SMOD_disregard_available - SMOD_disregard

        self.SMOD_disregard_available = remaining_SMOD_disregard

    def _apply_equity_disregard(self, prop):
        # if not prop.disputed:
        #     return

        prop['equity'] = max(prop['equity'] - self.equity_disregard_available, 0)

    def _reset_state(self):
        self.mortgage_disregard_available = constants.disposable_capital.MORTGAGE_DISREGARD
        self.SMOD_disregard_available = constants.disposable_capital.SMOD_DISREGARD
        self.equity_disregard_available = constants.disposable_capital.EQUITY_DISREGARD

        for prop in self.properties:
            prop['equity'] = 0

    def _calculate_property_capital(self):
        if not self.properties:
            return

        # calculating equities
        for other_property in self.other_properties:
            self._calculate_property_equity(other_property)

        self._calculate_property_equity(self.main_property)

        # applying SMOD disregard
        self._apply_SMOD_disregard(self.main_property)

        for other_property in self.other_properties:
            self._apply_SMOD_disregard(other_property)

        # applying equity disregard (to main home only)
        self._apply_equity_disregard(self.main_property)

    def calculate_capital(self):
        self._reset_state()
        self._calculate_property_capital()

        capital = 0
        # property capital
        for prop in self.properties:
            capital += prop['equity']

        # liquid capital
        capital += self.liquid_capital
        return capital


class EligibilityChecker(object):
    def __init__(self, case_data):
        super(EligibilityChecker, self).__init__()
        self.case_data = case_data

    @property
    def gross_income(self):
        if not hasattr(self, '_gross_income'):
            self._gross_income = self.case_data.total_income
        return self._gross_income

    @property
    def disposable_income(self):
        if not hasattr(self, '_disposable_income'):
            gross_income = self.gross_income

            if self.case_data.facts.has_partner:
                gross_income -= constants.disposable_income.PARTNER_ALLOWANCE

            # children

            # TODO 2 values for children...
            gross_income -= self.case_data.facts.dependant_children * constants.disposable_income.CHILD_ALLOWANCE

            # Tax + NI
            income_tax_and_ni = self.case_data.you.deductions.income_tax \
                              + self.case_data.you.deductions.national_insurance
            gross_income -= income_tax_and_ni
            if self.case_data.facts.should_aggregate_partner:
                income_tax_and_ni = self.case_data.partner.deductions.income_tax \
                                  + self.case_data.partner.deductions.national_insurance
                gross_income -= income_tax_and_ni

            # maintenance 6.3
            gross_income -= self.case_data.you.deductions.maintenance
            if self.case_data.facts.should_aggregate_partner:
                gross_income -= self.case_data.partner.deductions.maintenance

            # housing
            mortgage_or_rent = self.case_data.you.deductions.mortgage  # excl housing benefit
            mortgage_or_rent += self.case_data.you.deductions.rent
            if self.case_data.facts.should_aggregate_partner:
                mortgage_or_rent += self.case_data.partner.deductions.mortgage
                mortgage_or_rent += self.case_data.partner.deductions.rent

            if not self.case_data.facts.dependant_children:
                mortgage_or_rent = min(mortgage_or_rent, constants.disposable_income.CHILDLESS_HOUSING_CAP)
            gross_income -= mortgage_or_rent

            if self.case_data.you.income.has_employment_earnings and not self.case_data.you.income.self_employed:
                gross_income -= constants.disposable_income.EMPLOYMENT_COSTS_ALLOWANCE

            if self.case_data.facts.has_partner and self.case_data.facts.should_aggregate_partner:
                if self.case_data.partner.income.has_employment_earnings and not self.case_data.partner.income.self_employed:
                    gross_income -= constants.disposable_income.EMPLOYMENT_COSTS_ALLOWANCE

            # criminal
            gross_income -= self.case_data.you.deductions.criminal_legalaid_contributions  # not for now
            if self.case_data.facts.should_aggregate_partner:
                gross_income -= self.case_data.partner.deductions.criminal_legalaid_contributions

            # childcare 6.5.2
            gross_income -= self.case_data.you.deductions.childcare
            if self.case_data.facts.should_aggregate_partner:
                gross_income -= self.case_data.partner.deductions.childcare

            self._disposable_income = gross_income

        return self._disposable_income

    @property
    def disposable_capital_assets(self):
        if not hasattr(self, '_disposable_capital_assets'):
            # NOTE: problem in case of disputed partner (and joined savings/assets)

            capital_calc = CapitalCalculator(
                properties=self.case_data.property_data,
                liquid_capital=0 if self.case_data.facts.has_disputed_partner else self.case_data.liquid_capital

            )
            disposable_capital = capital_calc.calculate_capital()

            # if not self.case_data.facts.has_disputed_partner:
            #     disposable_capital += self.case_data.liquid_capital
            # else:
            #     # big TODO
            #     raise NotImplementedError('Not supported yet')

            if self.case_data.facts.is_you_or_your_partner_over_60:
                disposable_capital -= constants.disposable_capital.PENSIONER_DISREGARD_LIMIT_LEVELS.get(max(self.disposable_income, 0), 0)

            disposable_capital = max(disposable_capital, 0)

            self._disposable_capital_assets = disposable_capital

        return self._disposable_capital_assets

    def is_gross_income_eligible(self):
        if self.case_data.facts.on_passported_benefits:
            return True

        limit = constants.gross_income.get_limit(self.case_data.facts.dependant_children)
        return self.gross_income <= limit

    def is_disposable_income_eligible(self):
        if self.case_data.facts.on_passported_benefits:
            return True

        return self.disposable_income <= constants.disposable_income.LIMIT

    def is_disposable_capital_eligible(self):
        limit = constants.disposable_capital.get_limit(self.case_data.category)
        return self.disposable_capital_assets <= limit

    def is_eligible(self):
        if self.case_data.facts.is_under_eighteen:
            return True

        if self.case_data.facts.on_nass_benefits:
            return True

        if not self.is_disposable_capital_eligible():
            return False

        if not self.is_gross_income_eligible():
            return False

        if not self.is_disposable_income_eligible():
            return False

        return True
