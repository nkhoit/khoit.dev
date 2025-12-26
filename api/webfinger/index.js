module.exports = async function (context, req) {
    const resource = req.query.resource;

    // Security: Reject requests for domains that aren't yours
    if (!resource || !resource.endsWith('@khoit.dev')) {
        context.res = {
            status: 400,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            body: JSON.stringify({
                error: "Invalid resource domain."
            })
        };
        return;
    }

    // Dynamic Response: Echo back the requested 'resource' (subject)
    const responseBody = {
        "subject": resource,
        "links": [
            {
                "rel": "http://openid.net/specs/connect/1.0/issuer",
                "href": "https://clerk.khoit.dev"
            }
        ]
    };

    context.res = {
        status: 200,
        headers: {
            "Content-Type": "application/jrd+json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        },
        body: JSON.stringify(responseBody)
    };
};