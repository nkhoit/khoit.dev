module.exports = async function (context, req) {
    const resource = req.query.resource;

    // Security: Reject requests for domains that aren't yours
    if (!resource || !resource.endsWith('@khoit.dev')) {
        context.res = {
            status: 400,
            body: "Invalid resource domain."
        };
        return;
    }

    // Dynamic Response: Echo back the requested 'resource' (subject)
    context.res = {
        headers: {
            "Content-Type": "application/jrd+json"
        },
        body: {
            "subject": resource,
            "links": [
                {
                    "rel": "http://openid.net/specs/connect/1.0/issuer",
                    "href": "https://clerk.khoit.dev" // Your Clerk Issuer
                }
            ]
        }
    };
};