export async function onRequestPost(context) {
    const { request, env } = context;

    let data;
    try {
        data = await request.formData();
    } catch {
        return Response.json({ error: 'Invalid form data' }, { status: 400 });
    }

    const company = (data.get('company') || '').trim();
    const source = (data.get('source') || '').trim();
    const headcount = parseInt(data.get('headcount') || '0');

    if (!company || !source || !headcount) {
        return Response.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const submission = {
        company,
        headcount,
        date: data.get('date') || '',
        source,
        notes: (data.get('notes') || '').trim(),
        email: (data.get('email') || '').trim(),
        submitted_at: new Date().toISOString(),
        status: 'pending'
    };

    const id = `submission_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

    if (env.SUBMISSIONS) {
        await env.SUBMISSIONS.put(id, JSON.stringify(submission));
    }

    return Response.json({ success: true, id });
}
