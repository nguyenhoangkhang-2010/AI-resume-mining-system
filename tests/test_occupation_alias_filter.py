from app.knowledge_base.providers.onet_occupation_provider import (
    ONETOccupationProvider
)

from app.knowledge_base.services.occupation_alias_filter import (
    OccupationAliasFilter
)

from app.knowledge_base.services.occupation_alias_frequency import (
    OccupationAliasFrequencyAnalyzer
)


def test_occupation_alias_filter():

    provider = ONETOccupationProvider()

    raw_occupations = provider.load_raw()

    print(
        "Raw occupations:",
        len(raw_occupations)
    )


    analyzer = OccupationAliasFrequencyAnalyzer()

    token_coverage = analyzer.token_coverage(
        raw_occupations
    )


    alias_filter = OccupationAliasFilter()


    removed = 0
    original = 0
    filtered_total = 0


    removed_examples = []


    for occupation in raw_occupations:

        before = len(
            occupation.aliases
        )


        after_aliases = (
            alias_filter.filter(
                canonical=occupation.name,
                aliases=occupation.aliases,
                token_coverage=token_coverage,
                total_occupations=len(raw_occupations)
            )
        )


        after = len(after_aliases)


        original += before
        filtered_total += after

        removed += before - after


        for alias in occupation.aliases:
            if alias not in after_aliases:
                removed_examples.append(
                    (
                        occupation.name,
                        alias
                    )
                )


    print()
    print(
        "Original aliases:",
        original
    )

    print(
        "Filtered aliases:",
        filtered_total
    )

    print(
        "Removed aliases:",
        removed
    )


    print()
    print(
        "Removed examples:"
    )


    for item in removed_examples[:20]:
        print("-", item)


    assert len(raw_occupations) == 1016