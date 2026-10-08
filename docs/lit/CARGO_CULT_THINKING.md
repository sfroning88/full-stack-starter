# Cargo Cult Thinking

## Cargo Cult Software Engineering

Richard Feynman warned about scientists who follow the form of science without the substance. The same problem is everywhere in software: teams adopting practices they don't understand, hoping the results will follow.

Last year, a mentor of mine recommended I read Richard Feynman's 1974 commencement address at Caltech. It's about what Feynman called "cargo cult science," and it changed how I think about work.

During the Second World War, Pacific islanders had watched military planes land on improvised airstrips, delivering cargo: food, equipment, supplies. After the war ended and the planes stopped coming, some islanders built replica runways out of bamboo, lit signal fires, and carved wooden headphones to wear while sitting in control towers they'd built from straw. They'd replicated the form perfectly. But no planes came.

Feynman's point wasn't about the islanders. It was about scientists who follow the rituals of scientific inquiry (the conferences, the papers, the methodology sections) without the intellectual honesty that makes science actually work. They do everything that looks right. But the planes don't land.

I think about this regularly in software engineering.

### The Rituals We Perform

Watch a typical software team and you'll see rituals everywhere. Daily standups where everyone recites what they did yesterday without anyone actually listening. Sprint retrospectives that produce "fugazi" action items nobody follows up on. Code reviews that check formatting but not logic. Architecture decision records that get written after the decision is already made. Story points that get reported up to management as if they were units of measurement.

Each of these practices exists because someone, somewhere, did it for a real reason and it worked. Standups originated in teams that genuinely needed to coordinate across dependencies every morning. Retrospectives were invented by teams that took continuous improvement seriously. Code reviews catch real bugs... when the reviewer actually reads the code.

But when you adopt the practice without understanding the underlying reason, you get cargo cult engineering. You get the bamboo runway. You get the ritual without the result.

### Why This Happens

The pattern is predictable. A successful company publishes a blog post about how they work. "This is how Spotify organises engineering teams." "This is how Google does code review." "This is how Netflix handles deployments." The industry reads it and copies the form: the squad model, the review checklist, the deployment pipeline.

What they don't copy is the context. Spotify's squad model emerged from specific scaling challenges with specific people and specific technical constraints. Google's code review culture is embedded in decades of institutional knowledge and tooling. Netflix's deployment confidence comes from years of investment in chaos engineering and observability.

Lifting a practice from one context and dropping it into another without understanding why it works is exactly the cargo cult problem. You've built the runway. But the planes aren't coming because the planes were never about the runway; they were about the logistics network, the supply chain, the war effort behind them.

### What It Looks Like in Practice

I see this most clearly with Agile. The Agile Manifesto was written by people who valued individuals and interactions over processes and tools. Twenty years later, "being Agile" mostly means buying Jira licenses and having a certified Scrum Master run your ceremonies. The form is immaculate. The substance (the willingness to adapt, to communicate honestly, to deliver working software frequently because you care about the outcome) is often completely absent.

Microservices are another example. Amazon and Netflix decomposed their monoliths into services because they had specific scaling and organisational problems that monoliths couldn't solve. They did it gradually, painfully, over years. But the industry cargo-culted the result: "successful companies use microservices, therefore we should use microservices." Teams of five people split their simple CRUD application into twelve services, added a message broker, a service mesh, and distributed tracing, then spent the next year debugging network issues that didn't exist when it was one application.

The same thing happens with infrastructure as code, with test-driven development, with domain-driven design, with every practice that has a name. The name makes it easy to adopt the form. The understanding is the part that takes effort.

### Feynman's Antidote

Feynman's prescription was simple: intellectual honesty. He called it "a kind of scientific integrity, a principle of scientific thought that corresponds to a kind of utter honesty." The first principle is that you must not fool yourself, and you are the easiest person to fool.

In software terms, this means asking uncomfortable questions. Not "are we doing standups?" but "are our standups actually helping us coordinate?" Not "do we have microservices?" but "are our service boundaries in the right places, and how would we know if they weren't?" Not "are we Agile?" but "when was the last time we changed our process because it wasn't working?"

It means being honest about what you don't understand. If you're adopting a practice because someone you respect recommended it, that's fine, but you should know that's what you're doing, and you should be watching for signs that it's not working in your context.

It means measuring outcomes, not activities. The team that ships reliable software and responds quickly to user needs is engineering well, regardless of whether they have sprints or standups or story points. The team that performs every ceremony perfectly but ships late and buggy has built a beautiful bamboo runway.

### The Practices I've Kept

I'm not arguing against practices; I'm arguing against unreflective adoption.

I try to ensure that every practice I follow has a specific, articulable reason. If I can't explain why I do something, that's a signal that I might be cargo-culting it.

### The Test for Cargo Cult Software Engineering

Here's a simple test for whether a practice is genuine or cargo cult in your team: can the people performing it explain why they're doing it, in terms of the specific problem it solves for them?

Not "we do standups because Scrum says so." Not "we use microservices because that's the modern architecture." Not "we write tests because best practices."

But: "We do a quick sync each morning because the data pipeline team and the frontend team keep stepping on each other's database migrations, and this catches it before it becomes a merge conflict." That's a real reason. That's a practice that solves a problem the team actually has.

If you can't articulate the reason, you have two options: figure out the reason, or stop doing the thing. Both are better than continuing to carve wooden headphones and waiting for planes that aren't coming.

## Knowing How Isn't Knowing Why

I started code reviewing for a junior developer a few months ago. It taught me more about my own understanding than I expected, and revealed a model of learning that changes how I think about software knowledge.

A few months ago, I started code reviewing for a junior developer on our team. I expected it to be straightforward: read the code, spot the issues, talk them through on a call. I'd been writing production software for a while. How hard could it be to explain what I already knew?

It turned out to be one of the most revealing experiences of my career so far. Not because the code was difficult, but because the act of teaching exposed gaps in my own understanding that I didn't know existed.

### The Gap Between Doing and Explaining

There's a specific moment that stays with me. I was reviewing some code where the junior had written a service that mixed data fetching with business logic. I knew instinctively that this was wrong. I could feel it. If I'd been writing the code myself, I would have separated those concerns without thinking. It was automatic.

But when we got on a call to discuss it, I froze. "Because it's better" isn't feedback. "Because separation of concerns" is just naming the principle without explaining it. I needed to articulate the specific reason this separation mattered in this context: what would go wrong if we didn't do it, what it would cost us later, what it would make easier.

That moment taught me something important: there's a difference between being able to apply a rule and being able to explain why the rule exists.

### How Understanding Develops

Through code reviewing, and many conversations with my mentor about this exact problem, I've come to think about software knowledge as moving through stages that are easier to describe than to name. The first is learning by accumulation: you watch someone more experienced, you see them make a choice, and later you see them make the same kind of choice in a different context. Your brain starts to pattern-match without anyone stating the rule. This is how my mentor taught me: not by explaining SOLID principles, but by walking through specific instances of applying them in real code. The learning was implicit. Here's how I structured this service, here's why I split this module, here's what I changed.

At some point, you can apply the pattern yourself. You write code that separates concerns, keeps functions small, names things well, but if someone asks why, you struggle to get past "it feels right" or "that's how it should be done." You've internalised the rule but you can't externalise it. This is where most competent developers sit for years, and it's a perfectly functional place to be.

The jump is when you can not only apply the rule, but explain the principle behind it, describe the contexts where it does and doesn't apply, generate new instances that illustrate it. You've moved from knowing-how to knowing-that. You can defend it, and critically, you know when to break it.

That jump is what code reviewing forced on me.

### The Feedback Loop

Here's where I originally had a simpler model in my head: you do first, then you read to understand what you did. Practice, then theory. But I've come to think that's too linear.

What actually happens is more like a feedback loop. You see instances and develop tacit knowledge. Then you read something, an article about dependency injection or a chapter on domain-driven design, and it clicks because you've already felt the problem it solves. That reading reshapes how you see the next instance. You apply the refined understanding, encounter a new edge case, go back to reading with a sharper question, and the cycle continues.

Reading without doing produces cargo cult understanding. You can recite the principles but you've never felt the pain they address. You know that "you should favour composition over inheritance" but you've never been burned by a deep inheritance hierarchy that made a simple change cascade through twelve files.

Doing without reading produces superstition. You know that something works, but you might attribute it to the wrong cause. You always write small functions because a senior once told you to, but you think it's about readability when it's actually about testability. The practice is correct but the mental model is wrong; wrong mental models eventually lead you to apply the rule in contexts where it doesn't help, or fail to apply it in contexts where it would.

The strongest developers alternate between the two rapidly. They try something, read about why it worked, try a variation, read a different perspective, and so on. The theory and the practice aren't sequential; they're interleaved, each one sharpening the other.

### What Code Reviewing Taught the Reviewer

The irony is that reviewing code for a junior developer pushed me to a deeper understanding of several concepts I thought I already had.

When I had to explain why we inject dependencies rather than instantiate them directly, I realised my own understanding of dependency injection was more mechanical than principled. I knew the pattern, but articulating the specific benefit required me to think about it more carefully than I ever had when just writing the code.

When I had to explain why a certain function should be extracted, I couldn't just say "it's too long." I had to identify the specific reason: this function is doing two things with different rates of change, and when one changes, the other shouldn't have to.

Each of these explanations forced a precision of thought that writing code alone never demanded. The junior's questions were the best forcing function I'd encountered. Not because they were sophisticated, but because they were honest. "Why?" is the most powerful question in software development, and it's the one we stop asking once we reach unconscious competence.

### The Implication for How We Teach

This has practical consequences for how learning gets structured in software teams.

Don't start with the textbook. If someone hasn't felt the pain of tightly coupled code, explaining the dependency inversion principle is just noise. It'll sound theoretically correct and practically meaningless. Let them write the tightly coupled code, let them experience the change that cascades everywhere, and then show them the principle. The learning sticks because it has a hook to attach to.

But don't stop at the doing either. A team that only learns through osmosis, watching seniors and picking up habits, will develop capable practitioners who can't explain their decisions. That's fine until they need to make a decision in unfamiliar territory, where there's no pattern to match against. That's when the rationalised understanding matters.

The opportunities for that kind of deeper learning are obvious once you look: code reviews, pair programming where the more experienced person narrates their thinking, architecture decision records where you have to write down why you chose an approach, and team discussions where practices are questioned rather than assumed.

### The Test for Knowing Why

Here's a test I now apply to myself: for any practice I follow, can I explain not just what I do, but why I do it, and when I would stop doing it?

"I write unit tests" is a what. "Because they let me refactor with confidence" is getting somewhere. "When the cost of maintaining them exceeds the confidence they provide (which happens with highly volatile UI code), I'd stop" is the full thing.

The junior developer doesn't know it, but their code reviews have been a great learning experience for me. Not because they taught me new techniques, but because they forced me to understand the ones I already had.

## The Pragmatist’s Razor

Cargo cult engineering is adopting practices without understanding. But there's an equal and opposite failure: the engineer so principled they forget they're building software for people, not for architecture diagrams.

The cargo cult problem is easy to describe: you adopt a practice you don't understand, and when it fails you don't know why. But there's an equal and opposite failure that's harder to see: understanding a practice perfectly, and applying it in every context regardless of whether the problem it solves exists there.

The same standard of justification that applies to adopting a practice applies to how rigidly you apply it. The decision to relax a principle in a given context is not the absence of rigour. It is a higher form of it.

### Two Failure Modes, Not One

The cargo cult post described a single failure: practices without understanding. But there are two distinct ways to misapply knowledge of a practice.

Failure mode one: applying a practice you don't understand. This is the cargo cult problem. You adopt microservices because successful companies use microservices. You don't know what problem microservices solve, so you can't evaluate whether you have that problem. The practice fails, and you don't know why.

Failure mode two: applying a practice you do understand, in a context where the problem it solves doesn't exist. This is different. You understand that microservices solve independent deployability at scale. You understand the trade-offs. But your team is five people, your deployment pipeline is simple, and you have no scaling pressure. You apply the practice anyway, because the principle says you should, and principles are principles.

The first failure is ignorance. The second is rigidity. They produce different symptoms but the same outcome: wasted effort and systems that don't serve their users well.

The cargo cult test asks: "can you explain why you're doing this?" The pragmatist's test extends it: "can you explain why you're doing this here, given these constraints?"

### Defining Pragmatism

Pragmatism gets confused with two other things. The first is recklessness: taking shortcuts without awareness of what you're giving up, decisions where you can't name the trade-off because you didn't consider there was one. Pragmatism is not that. The second confusion is with the absence of principles altogether. Pragmatism is not that either. It's the application of an additional principle: that the value of any practice is conditional on context, and that context must be evaluated, not assumed.

A pragmatic decision has three properties:

1. You can name the principle you're choosing not to follow.
2. You can explain why the problem that principle addresses is either absent or less important than a competing concern in this specific situation.
3. You can describe the conditions under which you would revisit that decision.

If any of these is missing, the decision isn't pragmatic. It's either reckless (you can't name the trade-off) or arbitrary (you can't explain the reasoning).

### The Spectrum

The reckless engineer and the purist are mirror images of each other. The reckless engineer makes decisions without reference to principles at all; shortcuts are taken because they're faster, not because they've been evaluated. The question "what are we giving up?" never gets asked. The purist is the inverse: principles are applied uniformly regardless of context, because they're treated as unconditional laws rather than responses to specific problems. The question "does this problem exist here?" never gets asked either.

Pragmatism sits between them, but that positioning is misleading if you read it as "easier." It's actually the most demanding position on the spectrum. The purist can apply the same rules everywhere without thinking. The reckless engineer can ignore rules everywhere without thinking. The pragmatist has to think every time. Thinking takes more effort than either consistency or indifference.

### When to Hold and When to Relax

Three things tend to determine it. The first is the cost asymmetry of being wrong. Some principles protect against failures that are cheap to fix; others protect against failures that aren't. Input validation, authentication, data integrity: the cost of applying these correctly is small; the cost of not applying them can be enormous. When the downside of relaxing a principle significantly outweighs the cost of following it, that asymmetry does most of the reasoning for you.

The second is whether the shortcut is local or structural. Some deviations affect one file, one function, one component; if you're wrong, you fix it in an afternoon. Others create coupling that compounds: changing the database schema now requires changing the API, the frontend, the deployment pipeline. The first kind is often pragmatic. The second rarely is, because the cost isn't borne at the moment of the decision. It's deferred, and deferred costs grow.

The third is whether you can articulate the trade-off precisely. Not vaguely. Precisely. "I'm choosing not to do X because the problem X addresses doesn't apply here, and applying it anyway would cost Y." If you can't reach that sentence, you're not being pragmatic. You're skipping something because it's inconvenient, which is recklessness with a better vocabulary.

### The Symmetry

This reveals a symmetry between the cargo cult problem and the purism problem that I didn't fully see when I wrote the first post.

The cargo cult test: every practice should have a specific, articulable reason for being followed.

The pragmatist's extension: every deviation from a practice should have a specific, articulable reason for being made.

These are the same test applied in opposite directions. Together they form a single standard: every engineering decision, whether to follow a principle or to deviate from it, requires a justification that references the specific context.

The cargo cult engineer fails the first test. They follow practices without reasons. The purist fails the second test. They refuse to deviate without acknowledging that reasons could exist. The pragmatist passes both.

### Pragmatism as the Harder Skill

This framing explains why pragmatism is harder to develop than either purism or recklessness.

Recklessness requires no knowledge of principles. You just do what seems easiest.

Purism requires knowledge of principles, but not judgement about their applicability. You learn the rules and apply them. This feels rigorous, and it is, in the same way that applying a formula without checking whether the assumptions hold is rigorous. It is consistent without being correct.

Pragmatism requires knowledge of principles and the ability to evaluate their relevance to a specific context. You need to understand what problem the principle solves well enough to recognise when that problem is absent. This means understanding the principle more deeply than the purist does, not less.

The purist knows that you should separate concerns. The pragmatist knows why you separate concerns (because different rates of change in the same unit create cascading modifications), and can therefore identify situations where the rates of change are actually the same and separation would add complexity without benefit.

This is why I think pragmatism is better understood as a deeper engagement with principles rather than a looser one. The pragmatist doesn't care less about good engineering. They care enough to distinguish between the principle and the context that gives it value.

### A Decision Framework

When I'm evaluating a decision like this, three questions do most of the work. What specifically am I trading off, not vaguely "code quality" but precisely: what property of the system, what future capability am I choosing to forgo? If this turns out to be wrong, how expensive is it to reverse: an afternoon's work or something baked into the architecture? And can I explain it in six months, not just to a colleague but to my future self who has forgotten the context?

If all three answers are clear, the decision is defensible whether it follows the principle or deviates from it. If any is vague, that's a signal to think harder before committing.

If every engineering decision requires a justification that references context, the next question follows: how do you know whether that justification is actually correct? It's not enough to have a reason. The reason has to be testable. That's where the series goes next.

## Alive to Guess Again

Karl Popper argued that a theory which can't be proven wrong isn't really saying anything. The same is true of engineering practices: if you aren't actively trying to break them, you don't know whether they're working.

There's a problem with justification that I haven't addressed. You can justify almost anything if you're allowed to be vague enough. "We do standups because they improve communication." "We write tests because they improve quality." "We use microservices because they improve scalability." These sound like reasons. They have the shape of reasons. But they're missing something important.

Nobody is trying to prove them wrong.

### Popper's Razor

Karl Popper was a philosopher of science who spent most of his career on a single question: what separates real science from things that merely look like science? His answer was falsifiability, but the idea goes deeper than most people realise when they first encounter it.

Popper wasn't just saying that theories should be testable. He was saying that science progresses by actively trying to destroy its own theories. You accept a theory provisionally, as the best available explanation, and then you do everything you can to break it. You don't test it in the easy cases. You test it at the extremes, in the conditions where it's most likely to fail. If it survives serious attempts at refutation, it earns its place. Not permanently, but for now. The moment it does fail, you discard it and move on.

The distinction matters. Proving gravity by dropping a ball is trivial. Everyone already knows the ball will fall. The real test is at the boundaries: near a black hole, at quantum scales, in the conditions where the theory might actually break down. Easy confirmations tell you nothing. Hard tests are where knowledge lives.

Popper's classic examples were astrology and certain readings of Freudian psychoanalysis. An astrologer can explain any outcome after the fact. If the prediction was wrong, there's always a reason: another planet was in retrograde, the birth time was imprecise, the subject wasn't receptive. The theory never fails because it can absorb any result. Contrast this with Einstein's general relativity, which made a specific, testable prediction about how light bends around massive objects. If the 1919 eclipse observations had shown no bending, the theory would have been wrong. That vulnerability is exactly what made it valuable.

Or as Popper put it: good tests kill flawed theories; we remain alive to guess again.

I encountered Popper through a recommendation from a mentor, and the moment I understood the argument, I started seeing unfalsifiable claims everywhere in software engineering. Worse, I started seeing them in my own work.

### The Unit Test Problem

Here's something I did that taught me this lesson concretely.

I was working on a system and decided it needed better test coverage. This felt like an obviously good decision. Tests improve quality. Everyone knows this. So I went through the existing codebase and wrote unit tests for the code that was already there.

The tests passed. Coverage went up. It felt productive. But I was doing the equivalent of dropping a ball and confirming that gravity works. Every test I wrote verified that the code did what the code already did. I was looking at an implementation, understanding its behaviour, and then writing an assertion that confirmed it. These were easy confirmations. They tested the theory ("this code is correct") in the most comfortable conditions possible: the normal inputs, the happy path, the cases I already knew worked.

What I never did was try to break it. I never asked: "what are the boundary conditions where this logic might fall apart? What inputs would expose a flaw in my assumptions? What's the black hole for this function?" I was accumulating confirmations, not attempting refutations.

The coverage number looked good. But the test suite was unfalsifiable in practice. It couldn't fail in a way that told me anything I didn't already know. If a test broke, it was because someone changed the implementation, not because it caught a genuine behavioural problem. The tests were a mirror held up to the code, reflecting it back at itself.

What I should have done is what TDD actually intends: define the expected behaviour first, then write code to satisfy it, and critically, include the edge cases and boundary conditions where the behaviour might break. A test that says "when a driver completes a session, their lap times are ranked and the fastest is marked" is testing a business rule at its core. But the Popperian step is the next one: what happens when two lap times are identical? What happens when the session has zero laps? What about a session with one lap? Those are the hard tests. Those are the ones that kill flawed implementations.

In a small team, you can't afford to write tests for the sake of coverage. Every test should encode a business rule that, if violated, would cause a real problem. And the most valuable tests are the ones that test that rule in the conditions where it's most likely to break, not the ones that confirm it works in the easy case.

### The Pattern Is Everywhere

Once I started looking for practices that had never survived a serious attempt at refutation, I couldn't stop finding them.

Standups. Most teams justify standups as "improving communication" or "keeping everyone aligned." These teams have never tried to falsify the claim. It's not enough to define what success looks like and then passively wait to see whether it happens. The Popperian approach is to actively look for failure. Ask the team: "Did anyone have a coordination problem this week that the standup should have caught but didn't? Did anyone sit through the standup already knowing everything that was said? Did anyone withhold a problem because the format didn't make it safe to raise?"

If you go looking for failure and can't find it, the practice has survived a genuine test. If you find failure immediately, you've learned something valuable. Either way, you know more than you did. But most teams never ask. The standup continues, provisionally accepted but never tested at the extremes. It becomes a ritual that cannot fail because nobody is trying to make it fail.

Code reviews. The justification is usually "catching bugs" or "knowledge sharing." But if you tracked what actually happens in your code reviews, you might find that 90% of comments are about formatting, naming, or style, and almost none catch logic errors. That's the easy test: "do reviews happen?" Yes. The hard test is: "has a code review ever caught a bug that would have reached production? How often? What kind of bugs?" If you go looking for that evidence and can't find it, the practice has been falsified. It's not doing what you claimed it does. Maybe it's doing something else that's valuable, but the original justification is dead and you should update it or drop the practice.

Retrospectives. Teams run retrospectives to "continuously improve." A serious attempt at refutation would be: pull up the action items from the last three retrospectives. How many were completed? How many led to a measurable change in how the team works? If the answer is "we don't track that," the practice has been insulated from failure. You've never tested it at the extremes. You've been dropping the ball and confirming that it falls.

### Provisional Acceptance

There's a subtlety in Popper's thinking that changes how I approach all of this. He didn't say that unfalsified theories are "true." He said they're provisionally accepted. They've survived testing so far, and they're the best explanation available, but they could be overturned tomorrow by new evidence. This provisionality is the whole point. The moment you treat a practice as permanently justified, you stop testing it.

This is the difference between "we do standups because they work" and "we do standups because they've survived our attempts to find evidence that they don't work, and we'll keep looking." The first is a settled belief. The second is a living hypothesis. The first can't be wrong. The second invites being wrong, because being wrong is how you learn.

The same principle applies to architectural decisions, technology choices, team structures, deployment processes. All of them should be held provisionally. All of them should be subjected to the hardest tests you can find, not the easiest. And all of them should be discardable when the evidence turns against them.

### Why This Is Hard

Unfalsifiable practices survive because actively trying to break your own processes is uncomfortable. If you define what failure looks like and then go looking for it, you might actually find it. That means admitting something isn't working, changing course, possibly having difficult conversations. It's much easier to keep the justification vague and the testing gentle.

Popper noticed the same dynamic in science. Unfalsifiable theories are popular because they're safe. They explain everything, predict nothing, and never require their proponents to change their minds. Falsifiable theories are dangerous. They put themselves on the line. But that danger is exactly what makes them capable of being useful.

The connection to the pragmatist's razor is direct. That post argued that every deviation from a principle needs a specific justification. This post adds: every justification needs to be tested at the extremes, not confirmed in the easy cases. And when a justification fails the test, you have to be willing to let it go. Good tests kill flawed practices. We remain alive to guess again.

I approach testing differently now. Before I write a test, I ask: "what business rule does this encode, and what inputs would break it?" Not the happy path. The edge cases. The boundary conditions. The black holes. Coverage as a metric has become almost irrelevant to me. What matters is whether each test represents a genuine attempt to falsify the assumption that the code is correct.

More broadly, I've started treating every practice as a provisional hypothesis rather than a settled decision. Standups, reviews, architectural patterns: they're all theories about what works, and they all deserve to be tested seriously, not just confirmed gently.

I don't always get this right. The pull toward easy confirmation is strong, and it takes discipline to actively seek evidence that you're wrong. But I think that discipline is what Popper was really arguing for. Not just testability as a logical property, but a habit of mind: the willingness to try to break your own beliefs, and the honesty to update them when they break.
