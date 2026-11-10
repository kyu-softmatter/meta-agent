"""NIST Chemistry WebBook: a stub. Nothing is fetched (tasks/007: "fetch from NIST" is not this task's).

    lookup(substance, quantity)  ->  {rows: [], degraded: [], gaps: [gap]}

The gap names the page a later task would read, so that a sheet says where a value was not looked for.
"""
BASE = "https://webbook.nist.gov/cgi/cbook.cgi"


def url_for(substance):
    return "%s?Name=%s&Units=SI" % (BASE, str(substance).strip().replace(" ", "+"))


def lookup(substance, quantity):
    url = url_for(substance)
    return {"rows": [], "degraded": [],
            "gaps": [{"what": "%s of %s" % (quantity, substance), "searched": [],
                      "reason": "the NIST WebBook adapter is a stub: it reads nothing",
                      "requires": "an adapter that reads %s, anonymously and read-only, under a task that opens it" % url}]}
